# D439 ADDENDUM — the spec's adverse-selection term was the wrong one; net capture is `fill × hs − (1 − fill) × chase`

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D439-ADDENDUM-the-adverse-selection-term-was-the-wrong-one-net-capture-is-fill-times-hs-minus-the-chase.md`. The H1 above is the full title.*

**Committed before the corrected run. The data, the fill rules and the predictions' subjects are
unchanged; the statistic that decides is corrected, and the reason is written here.**

## What the first run showed

Two things. The `HALF` grid the atlas panel carries is already in basis points (D303:
`corwin_schultz(...) / 2 * 1e4`); the runner multiplied by 1e4 again and printed half-spreads of
"335,154 bp". Trivial, fixed. And the spec's **adverse selection** — *filled-minus-unfilled
subsequent return* — came out at +125 bp same-day and +478 on shock days, which is not a cost of
passive execution; it is the information in the fill, and it is the same information whichever
way the position was entered.

## The correct accounting

A trader who wants the position either way compares two ways of getting it:
- **cross at the open**: entry `O + hs` every day;
- **passive at the open for 30 minutes, else cross at the 30-minute price `P30`**: on filled
  days entry `O` (saving `hs`); on unfilled days entry `P30 + hs`.

On filled days both strategies hold the same position from the same morning; the day's
subsequent return is common to both and cancels. The only differences are the saved half-spread
on filled days and the **chase** on unfilled days — the move from `O` to `P30`, which is positive
for a buy precisely because the order did not fill (the price never came down to it). So:

**net capture per order = `fill × hs − (1 − fill) × E[P30/O − 1 | unfilled]`**, sells mirrored;
and as a fraction of `hs`. The chase needs `P30` (the 09:45 bar's close), which the loader now
keeps. The old "filled-minus-unfilled" term is still printed, labelled **fill information**,
because it is the honest size of the selection a passive order lives with, and its rotation null
is kept for that.

## What changes in the predictions

X-c's subject becomes the chase: on unfilled days under through-5 the 30-minute move against the
order is predicted at **+15 to +40 bp** (unfilled means the price ran), so with fill rates near
90% the term is small, and **X-d becomes: net capture 0.5 to 0.8 of `hs` over all days**, falling
on shock days where the chase is largest. X-a is amended by the first run: a touch at the open is
filled 100% by construction (the open is inside the first bar's range), so touch-at-open is a
degenerate rule and through-δ is the measure.
