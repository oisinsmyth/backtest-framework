# Nulls, block length, and the p95

[← method index](00-index.md) · prev: [benchmark choice](01-benchmark-choice.md) · next: [replication and multiple testing](03-replication-and-multiple-testing.md)

**`H6` derived the block-length selector in closed form, verified it reproduces the source paper's own
published table in 5 of 6 cells, and transcribed the reference implementation line-for-line.** It is
the most directly repo-relevant brief in the tree — **and two of its results contradict standing
guidance in `CLAUDE.md`.**

---

## Block length — the inherited 20 is harmless in one place and dangerous in the other `[EXT]` `H6`

**`b = 20` is optimal for AR(1) ρ = 0.4499.** And **`b = 21` ⟺ ρ = 0.4718 — D106 and D229 differ by
0.022 in implied autocorrelation. They are the same number.**

| where it is used | verdict |
|---|---|
| **return-side statistics** | **5–15× too LONG, and it does not matter.** The selector returns median **1.3** for white noise, **1.5** for GARCH returns. Because the bias term is `−G/b`, over-long blocks only inflate variance: **SE noisy to 4.0% at b=20 against 1.8% at b=4.** **`H6` advises AGAINST running a sensitivity study** |
| **persistent-summand statistics** | **~6× too SHORT — the dangerous direction.** The identical GARCH path wanting `b̂ = 1.5` for its mean wants **`b̂ = 132` for its squared mean**; a correlation of two ρ = 0.98 conditioners wants **~157.** **Too-short blocks understate the long-run variance → narrower intervals, EASIER NULLS** |

**The selector's input is the statistic's INFLUENCE SERIES, not returns.** That is the sentence that
decides which half applies to any given probe.

> **`[OPEN]`, flagged rather than asserted:** this session's regime-conditioner calibration used **159
> blocks over ~4,187 bars ≈ 26 bars per block**, on correlations of slow-moving conditioners — the
> case `H6` says wants ~157. **If those conditioners are as persistent as they appeared, that probe's
> decisive line of |r| ≈ 0.15–0.16 is too lenient. NOT CHECKED.** Item 13 of
> [`../../README.md`](../../README.md).

## The one number that decides whether any of it bites, and nobody has it `[CONFLICT C5 / C17]`

**The daily autocorrelation of an equal-weighted US book.** Three readings, all standing:

| | |
|---|---|
| `H6` (R4) | searched and found **none citable** |
| `J3` (R5) | found **one — ρ = 20.22%, CRSP EW index, daily, 1964–93** — and judged it a within-month 20-observation average, 33 years stale, on a universe a floor removes. **`J3`'s judgement, recorded as such** |
| `K5` (R6) | **a MODERN figure exists — +0.01 to +0.06 full-sample on a `$2`-floored TAQ panel, INDISTINGUISHABLE FROM ZERO in 2001–08 with the significant values NEGATIVE.** A modern figure for the EW **index** specifically remains a confirmed absence |

> **`H6`'s two halves point in opposite directions, so which one applies is not a matter of judgement
> — it is one number nobody has. It is measurable HERE in minutes and has not been measured.** Item
> 14 of [`../../README.md`](../../README.md).

## `CLAUDE.md` says per-name rotations carry an irreducible p95 bias. They do not `[OPEN]` ▲

> **`H6`: random draws from a group, WITH THE IDENTITY INCLUDED and `p = (1+b)/(1+w)`, are EXACT for
> any `w`.** *"The fix is one character of code."* **`[NOT APPLIED — amending standing guidance is the
> principal's call.]`**

## The p95 premise holds — for the smaller reason `[EXT]` `H6`

At `B = 200`: **bias −0.026 sd toward the centre, sd 0.146 sd — variance beats bias 5.6×.**

**So D373's 2-SE rule is right and ~18% more conservative than advertised**, and **`B ≈ 1,790` buys
SE = 0.05 sd.** `[REPO]` compare [FINDINGS §48](../../../FINDINGS.md) — a 200-draw rotation null
cannot resolve a 0.1 bp/bar margin, and three studies decided verdicts on exactly that — and
[§49](../../../FINDINGS.md), where 10,000 draws put the ranking **164 SE** above its null.

## Two theorems worth knowing before designing a null

1. **The 26-offset finding is a theorem, not an observation.** With `#G = 26`, α = 0.05 rejects only
   on a strict maximum — **size exactly 1/26 = 0.0385** — and **α = 0.01 has power identically zero.**
2. **The selector silently breaks at ρ ≥ 0.95.** Both the Python and R implementations cap the
   lag-window bandwidth at ≈70 — **a cap that is not in the source paper** — truncating the key
   quantity to **29% of its true value at ρ = 0.98.** And the theorem assumes `b = o(√N)`;
   `√4,190 = 64.7`. **At ρ = 0.98 there are 42 effective observations in 4,190 bars. No block length
   fixes that.**

## An internal-consistency check that passed `[EXT]`→`[REPO]`

**~10 effective instruments across 1,573 names is exactly ρ̄ = 0.0994** under the design-effect
formula — matching [FINDINGS §11](../../../FINDINGS.md)'s 10.06. **Two routes, one number.**

## A citation hazard `[EXT]`

**A 1999 paper's stationary-bootstrap variance is WRONG (sign error), and a 2004 paper's bound plus
all four of its simulation tables are superseded.** Anything built on either needs re-deriving.

## `[REPO]` the null rules this programme already holds, unchanged by the above

| | |
|---|---|
| [§32](../../../FINDINGS.md) | **a null must live in the universe the strategy trades** |
| [§50](../../../FINDINGS.md) | **removing a book's best names tests nothing unless every null draw loses ITS OWN best names** — the verdict reverses when it does |
| `CLAUDE.md` | **where the null's group is finite and small, ENUMERATE it** — all four of D361's exact p95s came in **above** their published 200-draw values, and the one thin margin fell from **+6.4 to +0.52** |
| `CLAUDE.md` | **a random subset is never a control for a persistent selector** — it churns. **Randomise the PARTNER, not the membership** |

---

**Sources.** [`the-timestamp-round.md` §1.7](../../the-timestamp-round.md) ·
[`the-selection-round.md` §11 `C5`](../../the-selection-round.md) ·
[`the-reversal-round.md` §10 `C17`](../../the-reversal-round.md) ·
repo: [FINDINGS §11, §32, §48, §49, §50](../../../FINDINGS.md), D106, D229, D361, D373.
