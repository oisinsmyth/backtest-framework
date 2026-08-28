# D256 — The short arms and the take-profit overlay, on single names

**Status:** Pre-registered — committed BEFORE the runner exists **and before the fixture was
inspected**
**Date:** 2026-08-28
**Area:** Strategy research

---

## This record was written without looking at the fixture

[D252](D252-the-dead-inclusive-us-single-name-universe.md)'s build was **still running** when this
was written — the `.csv.gz` was growing mid-write and its `meta.json` was a stale artefact of an
earlier attempt. **So no cell, hurdle or prediction below was chosen with knowledge of the data.**
That is the strongest form of pre-registration this programme has managed and it happened by
accident of timing; it is recorded because the fixture's final shape must not be able to have
influenced the design.

**Consequence:** every fixture statistic below is a **placeholder to be filled at run time**.
Symbol count, span, dead share and effective breadth are reported in the RESULT, not assumed here.

---

## Why this study, and why it answers two questions at once

[FINDINGS.md §2](../FINDINGS.md) states the position this test resolves:

> **Idiosyncratic variance is where the short edge lives, and it is also what makes a short bleed
> at `sigma^2`.** Crypto has enough of the second to swamp the first by an order of magnitude.
> **A single-name equity universe sits between the two extremes.**

And [D255](D255-stops-and-targets-on-the-book.md) closed exit overlays on a measured ceiling whose
cause is a property of the *instrument*, not the overlay:

> The best level of 600, with perfect hindsight, improves S1 by **+0.017 Sharpe**, because
> **97.2% of its trades never travel far enough to be cut.**

**Reachability is precisely the quantity that should differ between a basket and a single name.**
So one fixture tests both claims, and neither is a re-run in the sense D253 and D255 were: **both
were closed *on the ETF universe* with the instrument named as the reason.**

---

## Part A — the short arms

Frozen exactly as [D253](D253-the-book-short-sides-on-crypto.md) ran them:

```
S1_short   position = -1 if hist_L > 0 AND md_L <= 0
S2_short   DOWNTREND := g_lo < 0 AND g_hi < 0; enter at onset, exit at age 63 or state end
C_short    both on one shared pool at 100% capital, FCFS on magnitude
```

Bar counts frozen at the book's values — Impulse 34/9, k=3, window 252, age cap 63.
**No parameter is varied. 3 cells.**

## Part B — the take-profit overlay on the long arms

Frozen exactly as [D255](D255-stops-and-targets-on-the-book.md) ran them, **take-profits only**.
D255 established the asymmetry on two independent controls — targets help, stops cut the entry
dip — and **a stop is not re-tested here**, which keeps the cell count honest.

```
TP levels   +10%, +20%, +30%    on S1, S2, C     = 9 cells
```

**Reachability is reported BEFORE any cell is scored**, exactly as D255 did, and is the number
this half of the study exists to produce.

**12 cells in total. Counted in full.**

---

## The ragged panel — the methodological work, specified before it is written

`load_panel` refuses a panel whose symbols have different bar counts, and **that requirement is
exactly what deletes dead names**, which is the whole point of D252's fixture. So a ragged loader
is required and its contract is fixed here:

1. **Per-symbol live windows.** A symbol contributes only between its own first and last bar.
   Outside that window its return is zero and **its position is forced to zero**.
2. **Equal weight over LIVE names, not over `n`.** The portfolio return at bar `t` is the mean over
   the names live at `t`. **Dividing by a constant `n` would silently shrink every early-period
   return** — the defect class that produced D244's "BTC alone at 1/35 weight" error.
3. **A delisting is an exit at the last available price, decided with no foreknowledge.** The rule
   may not see that a name dies. Positions are carried to the final bar and closed there.
4. **No forward-filling of prices.** A fabricated price is a fabricated return.

**These are asserted in code, not assumed.**

---

## Hurdles

- **H.** Matched-count rotation null at **≥95th percentile on Sharpe AND money**, both legs
  ([R10](../RULES.md)'s second corollary). Rotation must respect each symbol's live window.
- **V.** **Positive net CAGR** after fees, financing and borrow. Introduced by D253 because
  **H is a skill test and V is a viability test**; a cell clearing H alone is reported as a
  measurement, never as a result.
- **E.** ≥100 pooled entries and ≥30 per symbol.
- **`exposure x edge` reported for every cell**, per [FINDINGS §1a](../FINDINGS.md) — never the
  edge alone.
- **R10 concurrency**, actual against a per-symbol-rotated book, plus effective instruments.
- **Model-A ruin** per short cell: worst adverse bar and maximum survivable notional.
- **For Part B:** R7's matched-exit-count null, **plus the level-randomised null**
  (`scripts/null_overlay_levels.py`), **plus a best-of-N floor computed WITHIN each arm** —
  D255's floor was misconstructed across arms and that error is not repeated.

## Predictions, committed before the runner and before the fixture

| | prediction | confidence |
|---|---|---|
| **Z-a** | **Reachability is far higher than D255's ETF figures.** Over 15% of long-arm trades touch +20%, against 2.8% for S1 on ETFs | **~75%** |
| **Z-b** | **At least one short cell clears H** — the hypothesis says skill should appear here as it did on crypto | **~65%** |
| **Z-c** | **No short cell clears V.** The `sigma^2` tax is smaller than crypto's but single names are still far more volatile than ETFs | **~60%** |
| **Z-d** | **Hurdle E fails on every cell.** Entries scale with span, not universe size, and this span is ~16 years | **~70%** |
| **Z-e** | **R10 concurrency is materially LOWER than on ETFs or crypto** — clustering ratio under 2.5x against 4.08x, 4.37x and 3.02x previously. **This is a direct consequence of the hypothesis and the cleanest test in the study** | **~70%** |

**Z-e is the one that carries the mechanism.** If single names cluster as hard as ETFs, then the
diversification story is wrong about *this* universe too, and the whole line needs rethinking
rather than extending.

**Z-a and Z-c in tension is the expected outcome:** the overlay finds room to work while the short
arms remain unviable. That combination would say the instrument choice was right and the
*direction* was wrong.

## Stop

**Part A closes if no short cell clears H and V together.** **Part B closes if no target cell
clears its R7 null, the level null and the within-arm floor.** They close independently — one
surviving does not license further work on the other.

**No parameter sweeps, no additional levels, no second fixture cut, and D245's reserved cohort is
not touched.**

## Ledger

| count | N |
|---|---:|
| fresh — 3 short cells + 9 target cells | 12 |
| + reachability diagnostic (3 arms x 3 levels) | 21 |
| + carried from D255 | 46,007 |
| **total** | **46,028** |

---

## RESULT — both parts CLOSED, and the study falsifies the reason D255 gave for its own failure

**Produced:** 2026-08-28 · `uv run python scripts/run_book_single_names.py --sims 400` ·
`BOOK_SINGLE_NAMES_RESULTS.md`

**Fixture as built:** **1,580 names**, 4,187 bars, 2010-01-04 → 2026-08-26, **564 dead (35.7%)**,
delistings spread 7–66 per year. **135 of 1,580 symbols carry internal gaps** — caught by a
pre-run assertion (`AAV: window 2254 != bars 2252`) which forced indicators to be scattered to
each symbol's **actual** bar indices rather than a contiguous slice. A slice would have misaligned
every indicator on those 135 names by the gap width.

### Part B — reachability rose threefold and the overlay still hurts

| arm | trades | median max gain | **reach +20%** | *ETF (D255)* |
|---|---:|---:|---:|---:|
| S1 | 38,220 | +4.25% | **9.0%** | *2.8%* |
| S2 | 6,299 | +8.42% | **21.4%** | *9.7%* |
| C | 41,402 | +4.85% | **11.2%** | *4.2%* |

**Z-a is directionally right and numerically short** — reachability is 2–3x the ETF figure, but
the prediction was ">15% for the long arms" and only S2 clears.

**And every one of the nine take-profit cells hurts:**

| | TP10 | TP20 | TP30 |
|---|---:|---:|---:|
| S1 vs base | −0.016 | −0.005 | −0.006 |
| S2 vs base | **−0.073** | −0.026 | −0.005 |
| C vs base | **−0.051** | −0.020 | −0.011 |

**The harm is monotone in tightness, and the loosest target approaches neutral only by ceasing to
fire** (S2:TP30 cuts 726 of 6,299 trades for −0.005).

> **This falsifies D255's own explanation of its own result.** D255 attributed the +0.017 ceiling
> to reachability — *"97.2% of its trades never travel far enough to be cut."* **Here trades travel
> three times as far and the overlay is still harmful.** Reachability was never the binding
> constraint. **A take-profit on these rules is simply a bad exit**, and it approaches harmlessness
> only by becoming inert. [FINDINGS §5](../FINDINGS.md) is corrected accordingly.

### Part A — no skill on single names

| cell | exposure | CAGR | **exposure x edge** | H (Sharpe / money) | V | E |
|---|---:|---:|---:|---:|:--:|:--:|
| S1_short | 13.6% | −3.01% | −2.95% | 88.5th / 11.5th | n | n |
| S2_short | 7.7% | −1.13% | −1.11% | 90.2nd / 87.2nd | n | n |
| C_short | 18.1% | −3.52% | −3.43% | 83.5th / 17.0th | n | n |

**Z-b is FALSIFIED.** No cell clears H, and the best is S2_short at the 90.2nd/87.2nd. **On crypto
the identical rule reached the 98.7th.** Skill did *not* appear in the middle case, which is what
the hypothesis predicted it would.

**Z-c and Z-d confirmed** — no cell clears V, and E fails at a minimum of **1** entry per traded
symbol across 1,357 symbols.

### Z-e — falsified, and my measure was stated in the wrong units

**First a correction to my own prediction.** Z-e was stated as an `sd_ratio` under 2.5x. **That
statistic is not comparable across universes of different size** — with `n` names driven by one
factor it scales roughly as `sqrt(n)`, so the ETF-to-single-name jump from 3.02x to 9.64x is mostly
arithmetic, not evidence. **`max share of live names held` is the scale-free measure** and is what
should have been registered.

| book | max share of live held | universe |
|---|---:|---|
| crypto S1_short (D253) | **100%** | 34 names |
| **single names S1** | **76.5%** | **1,580 names** |
| ETF wedge (D249) | ~72% | 57 names |

**Single names cluster essentially as hard as ETFs.** A market-wide event takes down **76.5% of
1,580 individually-listed companies at once**.

### The finding, and it is the one worth carrying forward

> **An equal-weighted book over 1,580 single names IS a diversified basket.** The idiosyncratic
> variance exists at the **name** level and averages away at the **book** level. In building the
> universe the hypothesis asked for, we rebuilt the very diversification the hypothesis identified
> as the problem.

That reconciles the whole sequence: **crypto (34 names, little averaging) showed skill at the
98.7th percentile; single names (1,580 names, maximal averaging) show none.** It was never the
instrument's listing status — **it is how many of them you hold at once.**

**And it exposes a tension the programme has to face:** *the same averaging that buys statistical
confidence destroys the idiosyncratic edge being measured.* Concentration would preserve the edge
and collapse the sample; breadth preserves the sample and averages out the edge. **Hurdle E and
the short hypothesis pull in opposite directions**, and no universe choice resolves it.

### Scoring

| | prediction | outcome |
|---|---|---|
| **Z-a** | reachability >15% on the long arms | **PARTIAL** — 2–3x the ETF rate, but 9.0% / 21.4% / 11.2% |
| **Z-b** | ≥1 short cell clears H | **FALSIFIED** — best 90.2nd, against 98.7th on crypto |
| **Z-c** | no short cell clears V | **CONFIRMED** |
| **Z-d** | E fails everywhere | **CONFIRMED** — minimum of 1 |
| **Z-e** | concurrency materially lower | **FALSIFIED**, and the statistic was mis-specified |

**Three of five failed. Both load-bearing predictions failed**, and the study is worth more for it
than a confirmation would have been.

### The stop applies to both parts

**CLOSED.** No parameter sweeps, no additional levels, no second fixture cut. D245's reserved
cohort was never touched.

**What a future study would need is not a new universe but a different construction** — a
concentrated book, which collides with hurdle E, or a factor-neutral one, which D251 closed on
ETFs and which this fixture's breadth could now support.
