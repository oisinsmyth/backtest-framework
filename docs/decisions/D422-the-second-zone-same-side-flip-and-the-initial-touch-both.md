# D422 — the second zone: same-side, the flip claim, and the initial touch, both lenses

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D422-the-second-zone-same-side-flip-and-the-initial-touch-both-lenses.md`. The H1 above is the full title.*

**Status:** design and bar committed BEFORE the runner exists (R8). Result separately.
**Date:** 2026-09-10
**Area:** Strategy research · the candidate

**Number.** `D422`, by PICKUP's three-command procedure: D400–D421 used, `D407–D410` reserved
(`044f839`), `D390–D399` reserved for `worktree-signal-hunt-part2` (`945cbb5`, live 15 hours ago).
Master takes D422.

**The principal's standing decision holds:** no holdout until there is a tradeable indicator.
**This study is the first whose declared candidate condition, if met, would satisfy that rule.**

---

## 1. Why, and what D421 left open

[D421](D421-RESULT-the-breach-is-empty-depth-is-a-hump-and-the-second-zone.md) found
depth is a hump: the **second** zone touched on a name in twenty sessions pays double the first
and double the third-or-later (+20.14 pooled, **+45.62 in cell 2**, against +9.81 / +10.52 and
+29.87 / +17.88). It found it by looking, on one rung of three, with two wrinkles in the counter:

1. **Same-day sibling zones counted as two prior touches** for later events, inflating rung 3+.
2. **The count was side-blind** — a prior *supply* touch counted toward a *demand* zone's stack.

This study resolves the first and opens the second into a test. The principal asked that the
"supply becomes demand" claim be **tested rather than dismissed**, and that every arm run through
**both lenses**.

---

## 2. THE CONDITIONS — code, committed with this record

`scripts/d422_stack_flags.py`, committed alongside. **It reads no outcome.** Over the trailing 20
sessions before each touch, it counts **distinct prior touch days** on the name, by side:

| arm | condition | what it is |
|---|---|---|
| **STACK2-SAME — PRIMARY** | exactly one prior same-side touch day, no opposite-side | *the second demand zone in a decline* — the mechanism the principal articulated |
| STACK2-ANY — baseline | exactly one prior touch day of either side | D421's rung, wrinkle 2 fixed |
| **FLIP — the claim** | this zone's midpoint lies inside the band of a prior **opposite-side** zone on the name, touched within 60 sessions, **whose far edge was traded through** before today | *a level that was supply, was broken, and is now approached as demand* — the claim as it actually reads |
| STACK1 / STACK3+ | no prior touch day / two or more | the initial touch / the trend — the hump's other rungs |

**Why FLIP is defined on the level and not on the stack.** In this construction a zone dies at
its first touch, so *the same zone* can never flip. The claim's content is that the *price level*
changes role after a break. FLIP tests that: a new zone at the same price as a broken
opposite-side one. It is independent of the stack count and is also reported intersected with
STACK2-ANY.

### 2a. Stage 0 — computed before this was written; facts, not predictions

```
                     pooled           cell 2          cell 2 & 2018+
STACK1               32.5%  58,477    30.6%   7,974        5,015
STACK2-SAME          18.7%  33,735    24.5%   6,371        4,172
STACK2-ANY           35.2%  63,297    36.2%   9,411        6,100
STACK3+              32.4%  58,276    33.2%   8,639        5,597
FLIP                 22.8%  41,010    20.1%   5,232        3,424
FLIP ∩ STACK2-ANY           14,164             1,918
share of STACK2-ANY that is same-side: 53.3%
```

The distinct-day fix moved ~5 points of events from rung 3+ into rung 2, exactly where D421's
double-counting had put them. **D421's rung was half same-side and half not** — the side question
is a real split. **The primary has 4,172 events in cell 2's second half**: a +20 bp premium there
would sit at roughly 2 SE, which is why T1 is gated on the pooled second half and the cell-2
second half is reported beside it.

---

## 3. THE ARITHMETIC, before the bar

STACK2-SAME is 24.5% of cell 2 — about 1.5 touches a day against a 10-slot book that frees two —
so a *required* book runs near **75% utilisation** and pays roughly **4 bp/bar** in neutral cost.
At D421's rung-2 gross of +45.62 per trade, gross per bar would be ~7. **If the same-side rung
holds its number, this is a net-positive book.** If it doesn't, §5 says so first.

---

## 4. THE PER-TRADE LENS

| | condition |
|---|---|
| **T1** | **second half, 2018–2026, pooled:** `mean(r_base | STACK2-SAME) − mean(r_base | not)` **> 0 by 2 SE.** The half every prior edge shrank in is the gate, not a footnote |
| **T2** | **pooled, all years:** the same premium beats the **p95 of a within-day label permutation** — the STACK2-SAME labels shuffled among each day's events, 200 draws, so the cross-section, the calendar, every event's return and its cell-2 flag are held and only *which name is at the rung* is destroyed. Margin outside 2 SE of the p95 (D373) |

Reported and not gated: the full distribution of both populations (mean, median, win, symmetric
1% trim); the same two tests for **STACK2-ANY** and **FLIP**; the hump under distinct-day
counting, pooled and cell 2; cell 2 and cell 2 second-half for every arm; per year; the
concentration checks (names to half the P&L, top-year share) — **a rung that pays double is where
a few names or one year could be doing the work.**

### 4a. FLIP's declared reading

FLIP carries T1 and T2 at the same 2 SE, **secondary, unable to clear D422.** Declared now:

- **FLIP's pooled premium inside 2 SE of zero → the flip claim is dismissed on this construction**,
  in those words, with the number.
- **FLIP's pooled premium positive by 2 SE and its second half positive → the claim earns its own
  pre-registration** and nothing more.
- Either way, FLIP ∩ STACK2-ANY is reported: does a flipped level *add* to a second zone?

---

## 5. THE BOOK LENS — D419's simulator, FIXED exit, three seeds

D421 showed a *priority* does nothing on a full book and a *requirement* is the lever, so the
books are requirements. FIXED is reproduced bit-identically before any depth book runs.

| book | slots | pool |
|---|---|---|
| FIXED | 10, cell 2 | D419's cell-2 book |
| **SAME-REQUIRED** | 10, cell 2 | cell 2 ∩ STACK2-SAME |
| ANY-REQUIRED, FLIP-REQUIRED | 10, cell 2 | secondary |
| FIXED / SAME-REQUIRED / ANY-REQUIRED / FLIP-REQUIRED | 50, pooled | reported |

| | condition |
|---|---|
| **T3** | the **cell-2 SAME-REQUIRED** book is **net-positive** (mean over seeds) **and** its net exceeds the **p95 of a matched-count random-requirement control** — the same *number* of cell-2 events admitted at random, drawn once, 50 draws — margin outside 2 SE (D373) |

Utilisation, turnover, cost per bar, gross and per-trade mean reported for every book; `[RECON]`,
`[CHUNK]` inherited.

---

## 6. THE CANDIDATE CONDITION — declared now

**STACK2-SAME clears T1, T2 and T3.** All three. That, and only that, makes this construction a
**tradeable indicator by the principal's rule** and a candidate for `holdout2` — on the
second-half number, with the cost model still unverified against fills. Anything short of it is
recorded as what it is.

**Three arms at 2 SE is three chances, stated.** Only STACK2-SAME can clear.

---

## 7. Predictions — mechanism at low confidence, arithmetic at moderate

| | prediction | confidence |
|---|---|---|
| X-a | STACK2-SAME's pooled premium over not-SAME is **+8 to +14 bp** | moderate |
| X-b | its **second-half premium is positive at about half the pooled size** — the pattern every real number here has followed | low-moderate |
| **X-c** | **FLIP's pooled premium is inside 2 SE of zero** — D421's DEEP-2-only population (+4.95) says a broken level is a breakdown, not a support | low-moderate |
| **X-d** | **the cell-2 SAME-REQUIRED book is net-positive at 1–2 SE and inside its control's p95** — real, and not by enough | low-moderate |
| X-e | the hump persists under distinct-day counting: rung 2 > rung 1 and rung 2 > rung 3+, pooled and cell 2 | moderate |

**X-d is the study.** Three structural predictions were wrong today; these are held to
low-moderate accordingly, and the runner prints the decompositions that would refute each.

---

## 8. What this does not do

- **No holdout read** until §6 is met. No 15m data. No exit, no change to entry or hold.
- **No sweep.** The 20-session window and the 60-session flip life are declared once.
- **Does not claim independence from D421** — the rung was found there; the side split, the
  distinct-day count, the second-half gate and the book are what is new.
- **Does not recommend a disposition.** That is the principal's.

---

## 9. R13

Twenty-second look by object on price levels. **Twenty-one of twenty-one before it failed their
bar.** No new data spent.

**Cost: minutes; the controls are projected before they run.**
