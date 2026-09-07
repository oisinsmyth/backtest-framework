# D372 — equal weight is the incumbent sizing, declared as a baseline, and the hurdle any cleverer scheme must clear

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8). **Nothing here is a
result.** No cell has been scored under any sizing scheme other than the incumbent, and §6's
stage-0 diagnostic has not been run.
**Date:** 2026-09-07
**Area:** Book construction · strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

**Provenance:** raised while reading `docs/Youtube Transcrips/` (see `docs/youtube-lessons.md`).
The video that prompted it is worthless as evidence — it compares a low-volatility portfolio and
a high-volatility benchmark at *identical* leverage and reports the difference in drawdown as
skill. But it asked one question this programme has not answered: **why is every book here
equal-weighted, and has anything been tried against it?**

---

## 0. Why

Sizing in this programme is split across two lineages that have never met.

- The **breakout / crypto** lineage has inverse-volatility sizing built and swept:
  [D110](D110-vol-target-sizing-lives-in-the-weight.md) implements `InverseVolatilityWeight`
  (weight = target annual vol ÷ trailing realised vol, capped at 1.0× capital, on the
  [D44](D44-engine-enforces-a-warm-up-period.md) estimator ending at t−1),
  [D118](D118-vol-target-swept-not-assumed.md) sweeps the target rather than assuming it, and
  [D119](D119-risk-equalised-constant-fraction-benchmark.md) supplies a risk-equalised
  constant-fraction benchmark.
- The **cross-sectional single-name** lineage — every book in `docs/FINDINGS.md` that anyone
  would trade — is equal-weighted, and nothing has ever been run against it.

The gap is not that equal weight is wrong. It is that **equal weight was never chosen**. It is
what the kernel happened to do, it has never been named as a decision, and so no alternative has
ever had a hurdle to clear. This record names it and sets the hurdle.

## 1. What the incumbent actually is

From the kernel, [`scripts/run_d306_width_exits.py:240`](../../scripts/run_d306_width_exits.py):

> the book is `mean(long) - mean(short)`, so a trade's weight at bar t is **`1/n_t` for its own
> leg, NOT `1/depth`** — the two differ whenever a delisting leaves the leg short of its slots.

So the incumbent is **equal weight within each leg, renormalised every bar to the number of names
actually held**. Call it **`EW`**. Three properties worth stating because a challenger must
preserve or consciously break them:

1. **It is dead-inclusive-safe.** `1/n_t` rather than `1/depth` means a leg thinned by a delisting
   does not silently hold cash at the dead name's weight. On a fixture built to include the dead
   ([D252](D252-the-dead-inclusive-us-single-name-universe.md)) that is load-bearing, not cosmetic.
2. **It has no parameters.** Nothing to fit, nothing to sweep, nothing to overfit.
3. **It is the only sizing with a track record here.** Every number in `docs/FINDINGS.md`, every
   null, every cost convention, every era split was produced under `EW`.

## 2. The declaration

**`EW` is the baseline. Any proposed sizing scheme is a challenger and carries the burden of
proof.** A sizing change is not an implementation detail; it is a change to what the book *is*,
and it is admitted the same way a signal is — on a stated hurdle, against the same nulls, under
both cost conventions.

## 3. Why `EW` is a hard baseline and not a strawman

It should be said plainly that `EW` is dumb, and in four specific ways:

- **It ignores volatility.** A $6 biotech and a $200 megacap take the same weight, so their risk
  contributions differ by an order of magnitude.
- **It ignores correlation entirely.** Twenty names from one sector is twenty units of one bet.
- **It ignores conviction.** The rank-1 and the rank-20 name get identical weight, though the
  score that selected them is continuous and was thresholded only to fill slots.
- **It ignores price, and therefore cost.** Cost in bp scales inversely with price (CLAUDE.md,
  which killed [D284](D284-the-overnight-long.md) on exactly this), so **equal weight is unequal
  cost drag** — the
  cheap names carry the heaviest bp burden while contributing the same notional.

And yet the prior that it wins is strong, for reasons that have nothing to do with this programme
being attached to it:

- **Estimation error usually exceeds the optimisation gain.** DeMiguel, Garlappi and Uppal (2009)
  found `1/N` beat fourteen optimised allocation models out of sample across seven datasets. The
  covariance matrix is estimated; the naive weight is not.
- **`EW` cannot be overfit**, so it needs no multiplicity correction, no null of its own, and no
  holdout read. A swept challenger needs all three.
- **Every alternative below is a parameterised family**, so a win must be shown to be a win of the
  *family*, not of its argmax — the failure the moving-average video in `youtube-lessons.md`
  makes visible and does not correct.

## 4. The challengers

In the order I would run them, cheapest first. Each already exists in code or is a one-line
reweighting of the kernel's per-bar mean.

| tag | scheme | source |
|---|---|---|
| `IV` | inverse realised vol, capped at 1.0×, D44 estimator ending at t−1 | [D110](D110-vol-target-sizing-lives-in-the-weight.md) brick, ported to the cross-sectional kernel |
| `IVT` | `IV` with the vol target swept rather than assumed | [D118](D118-vol-target-swept-not-assumed.md) |
| `RE` | risk-equalised constant fraction | [D119](D119-risk-equalised-constant-fraction-benchmark.md) |
| `RW` | weight monotone in rank within the leg (conviction weighting) | new; the cheapest test of whether the score is continuous information or a threshold |

`RW` is listed last but is the most interesting, because it is the only one that tests whether the
*signal* carries more than a binary selection — and it is the only one not confounded with §5's
trap.

## 5. The trap a challenger must not fall into

**Inverse-vol sizing is confounded with the universe floor.** Low price correlates with high
realised volatility, so `IV` partially re-implements the $5 / dv28 floor of
[D339](D339-a-universe-floor-price-and-dollar-volume.md) by shrinking the same names the floor
excludes. A win for `IV` may therefore be the floor arriving a second time under a new name, not a
sizing effect.

The control is forced by CLAUDE.md's rule that **a control must share the treatment's nuisance**:
`IV` must be scored **on the already-floored universe**, and must additionally be compared against
a **price-rank sizing** `PR` that shrinks by price alone with no volatility input. If `PR` captures
most of `IV`'s gain, the effect is the floor, not the vol.

## 6. Stage 0 first, and it may end this

Before any sizing scheme is implemented, run the **volatility-decile split of contribution P&L** on
the current books, using the D339 census machinery unchanged — the same split it already computes
for price and dollar volume, with realised vol as a third axis.

This is a diagnostic, not a test: it makes **no prediction** and admits nothing. It is run first
because the census already tells us where to expect the answer. From
[D339 §1](D339-a-universe-floor-price-and-dollar-volume.md), on `retrace_leg`:

> 12.2% of trades entered below $5 average **+805 bp** a trade against **+76** outside, and carry
> **61.3%** of the P&L.

Sub-$5, bottom-decile-dollar-volume names are the high-volatility tail. So the live possibility is
that P&L is **monotone increasing in volatility decile**, in which case `IV` is arithmetically
guaranteed to remove most of the book's earnings and there is nothing to implement. That outcome is
not a failure of this record; it is the record's cheapest possible success, and it reframes the
books as harvesting a **volatility premium** rather than exercising selection skill — a different
object, priced differently, with different capacity.

There is direct precedent for that outcome:
[D210](D210-nothing-survives-holding-leg-size-constant.md) — *"nothing survives holding leg size
constant"* — where five features stopped predicting once size relative to ATR was held fixed.

## 7. The hurdle

A challenger is admitted over `EW` only if **all** of the following hold. The criterion in (1) is
a function of the capital, not of the sizing scheme, per `docs/RULES.md` §600–608.

1. **On the right statistic for the capital.** Dedicated capital → it must beat `EW` on **gross**;
   shared capital → on **Sharpe / edge per unit exposure**. Declared before the run, not chosen
   after.
2. **Net under both conventions**, PB and PUB, not gross alone — a sizing change moves cost per
   trade and edge per unit exposure in opposite directions, and CLAUDE.md requires saying which
   moved.
3. **Against the same nulls the book already carries** — the 24 rank rotations and D348's
   control A' per-name time rotation, with the sizing recomputed from the rotated score, exactly as
   [D355](D355-the-invalidation-exit-on-the-candidate-books.md) recomputes its percentile grid
   under the null. A sizing scheme scored against a null that keeps the observed weights is not a
   null.
4. **As a family, not an argmax.** For any swept parameter, report p50 and p95 across the sweep
   beside the best cell, per CLAUDE.md's reporting rule.
5. **Not a re-expression of the floor** — §5's `PR` comparison must show the gain survives.
6. **Both lenses, never on the same statistic.** Sizing changes the path-variant book without
   changing which trades exist, so the path-invariant reading should be *unchanged*. If it moves,
   the implementation is wrong and the run is void.

## 8. Assertions the runner must carry

Beyond the three standing runner assertions (lag audit in a second implementation, sign audit in
money, right-quantity):

- **[W1]** weights sum to 1.0 per leg per bar, to float tolerance, on every bar the leg is live.
- **[W2]** with the scheme's parameter set to its degenerate value, the book is **bit-identical**
  to `EW` — the same standard D369's kernel met. A challenger that cannot reproduce the incumbent
  exactly is not comparable to it.
- **[W3]** the vol input is lagged: it reads bars up to and including **t−1** (D44) and the
  scores are already lagged by the ranker, so the audit must confirm the sizing does **not**
  double-lag.
- **[W4]** `1/n_t` renormalisation survives — a leg thinned by a delisting must still sum to 1.0
  and must not hold implicit cash (§1.1).
- **[W5]** the self-test **raises** on a deliberately broken weighting (weights that sum to 2.0,
  and a weight vector computed from bar t). A self-test that cannot fail is worse than none.

## 9. What would make me abandon this

- §6's split comes back **monotone increasing in vol** → `IV`/`IVT`/`RE` are all dead on arrival;
  record the finding that the books are a volatility premium and stop.
- §6 comes back **flat** → the sizing question is real but the prize is small; run `RW` only,
  since conviction weighting is the only challenger not answered by a flat split.
- Any challenger requires a holdout read to distinguish it from `EW` → **do not spend it.**
  Sizing is not worth the programme's one read while the prop book is empty and the signal
  question is unsettled.

---

**Status footer.** No runner exists. No cell scored. No book proposed. Nothing in this record is
a result, and `EW` remains the incumbent until something beats it under §7.
