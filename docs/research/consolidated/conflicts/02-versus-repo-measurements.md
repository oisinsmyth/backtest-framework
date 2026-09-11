# Research versus what this repo has measured

[← index](../00-INDEX.md) · siblings: [register](01-register.md) · [agreements](03-agreements.md) · [inside briefs](04-inside-briefs.md)

**The ruling that governs this file, from the principal, 2026-09-10:** where external research
disagrees with a study already run here, **the repo's measurement is taken as true.** The research
reading is **kept, marked, and not deleted.** Only the principal retires either side.

**Twelve entries.** Three are settled in the repo's favour by a measurement that already exists;
four are not conflicts at all once the objects are named; five are open and cheap.

---

## R1 · The cost bar every research round reasons from is a superseded statistic

| | |
|---|---|
| `[EXT]` | all six rounds of campaign 1 and `K6` reason from *"this programme's **33.8 bp/side**"*, and campaign 2 inherits it |
| `[REPO]` | [FINDINGS §17](../../../FINDINGS.md) / **D332**: 33.8 was **D285's held mean of the single two-day Corwin–Schultz estimate**. That estimate is **clamped to exactly zero on 43.2% of all live name-bars**, uniformly across price and uncorrelated bar to bar. **Corwin and Schultz never use the single estimate** — they average the clamped daily estimates over a month. Universe median under the published convention **31.7 bp/side against 14.2** for the per-bar median every runner since D318 was charging; across 92 legs the published convention charges **2.03×** at the median (p10 1.40×, p90 3.31×) |

**Repo prevails.** 33.8 is not a wrong number — it is a **different statistic** from the one this
programme now charges, and *"which convention is TRUE is not decided, and cannot be from OHLC
alone."* **Every breakeven in the research tree quoted against "33.8" must be re-read against the
`PB`/`PUB` pair.** Detail: [cost/01](../cost/01-spread-estimation.md).

## R2 · The direction of the Corwin–Schultz error — three defects, not two `[CONFLICT C7]`

`[EXT]` `H4` (R4): Ardia–Guidotti–Kroencke find CS **understates** effective spreads for small
illiquid stocks, so 33.8 would be a **floor**. `[EXT]` `J5` (R5): the author's own program
**forward-fills the high and low** on no-trade days by re-anchoring the prior-day range — fabricated
input on exactly the halt/no-trade set. `C7` records these as pushing the interpretation in
different directions.

`[REPO]` D332 found a **third** mechanism, and it is the only one measured on this fixture: the
**zero clamp**. *"The zeros are noise, not a property of any name."*

**Not contradictory — three distinct defects in one estimator, all saying the charged number is not
the spread.** `[OPEN]`: the **EDGE** drop-in (closed form, same OHLC inputs, `bidask` on PyPI) has
never been run here. It is item 2 of [`../../README.md`](../../README.md) §"What is open" and it sets the
sign of every cost conclusion downstream.

## R3 · The overnight drift — research said artifact, the repo measured and it is not `[SETTLED]`

| | |
|---|---|
| `[EXT]` | `shorts/03` §1: Lachance (2021) shows opening order imbalance plus wider overnight spreads inflate ETF overnight returns by **2.54 bp/day = 6.61%/yr**, and correcting for microstructure eliminates **three quarters** of the ETF overnight/intraday gap. Our gap is **8.95 pts**; three quarters is 6.7. *"Our headline finding may be predominantly a trade-price artifact."* |
| `[REPO]` | [FINDINGS §58](../../../FINDINGS.md) / **D402**: reproduced D280's gap IC to five decimals; **17.58%** of 2.23M out-of-sample bars carry a contamination flag; removing **every** contaminated bar makes the edge **larger** (ALL clean −0.01746, `t` −4.49, **1.14× committed**, n 1.35M). And the discriminating gradient runs the wrong way for an artifact: gap IC is **1.8× stronger in the most liquid dollar-volume quintile** than the thinnest |

**Repo prevails; the research prerequisite is discharged.** Two things to keep beside it. **(a)** D402
tested stale and extreme opening *prints*; Lachance's channel is quoted-spread *width* at the open,
which was not tested identically — the liquidity gradient is evidence against that channel too, but
it is inference, not the same test. **(b)** D402 exists **because** the prop-firm research folder
demanded that test of its own C19-2 row and nobody had ever demanded it of ours. **The research
earned its keep by losing its own hypothesis.**

## R4 · The `$5` floor — the repo is right and its stated reason is the weaker one

| | |
|---|---|
| `[EXT]` | `J4` (R5): **81.7% of studies impose no price filter at all**; published levels are bimodal at `$1` and `$5` with **nothing above `$5` ever named**. Relative spread is **invariant to nominal price** away from the tick constraint — 11 of 12 matched tests insignificant at the `$5`–`$20` boundary — and this programme's names are **~7 ticks wide**, nowhere near it |
| `[REPO]` | [FINDINGS §22](../../../FINDINGS.md) / **D339**: the floor was adopted on a **census**, not on a spread argument. **25 of 47 books take more than half their P&L below `$5`; 35 of 47 top trades fail it; nine names supply the top trade of 30 books.** The floor fails 29.3% of live name-bars; the sub-`$5` share of the universe went 3% (2010) → 13% (2025). Three of four books **improve**. *"Replace beats starve"* is worth 3–6 bp/bar. **From D339 the floor is the declared universe** |

**No conflict on the decision; a conflict on the reason — and the research strengthens the repo.**
`J4` supplies the argument this programme never stated: **the `$5` screen is a SUBSTITUTE for
value-weighting** (*"value-weighting assigns only tiny weights to these stocks, which in turn do not
need to be excluded"*), and **this programme is equal-weighted, so the substitution is unavailable
and the floor does real work here that it does not do in the papers it was inherited from.**

`[OPEN]`, and measurable here: **no published work varies a price screen across levels** — every
sensitivity in the literature is binary at `$5`. The `$5`–`$10` band's contribution is unmeasured
everywhere and measurable on this fixture. Detail: [cost/03](../cost/03-price-floor-and-screens.md).

## R5 · `50/P` — standing guidance in `CLAUDE.md` rests on the wrong channel

`CLAUDE.md` reporting rule 3 requires splitting results on **price**, *"cost in bp scales inversely
with price; killed D284."* `[EXT]` `J4`: **that is true of the COMMISSION and false of the SPREAD.**
`[EXT]` `K5` sharpens the other side — the equal-weight **bias** leverage is **quadratic, ∝ 1/P²**,
sharper than the repo's linear note.

**The empirical verdict is untouched:** D284's cheap names lost money and that is `[REPO]`. What is
in doubt is **which channel** did it, and therefore whether the split is measuring what the rule
says it measures. **Amending standing guidance is the principal's call.**

## R6 · Block length 20 `[OPEN]`

`[REPO]` D106 and D229 both use `b = 20` (and, per `H6`, differ by 0.022 in implied
autocorrelation — *"they are the same number"*). `[EXT]` `H6`, closed form, reproducing the source
paper's table in 5 of 6 cells: **20 is 5–15× too LONG on return-side statistics and it does not
matter** (over-long blocks only inflate variance); **~6× too SHORT on persistent-summand
statistics** — a pair of ρ = 0.98 conditioners wants **~157** — *"the direction that makes nulls
easier."*

**This session's own regime-conditioner calibration used ~26 bars per block.** Never checked here.
And **the one input that decides whether any of it bites — the daily autocorrelation of an
equal-weighted book — has no citable modern figure** (`C5`/`C17`, three readings) and is **minutes to
compute here.** Detail: [method/02](../method/02-nulls-and-block-length.md).

## R7 · Per-name rotation bias — `H6` contradicts `CLAUDE.md` directly `[OPEN]`

`CLAUDE.md`: per-name rotations, `B`/`B_c` and `C` are not enumerable, so *"the bias stands and only
(i) or more draws touch it."* `[EXT]` `H6`: random draws from a group **with the identity included**
and `p = (1+b)/(1+w)` are **exact for any `w`**. *"The fix is one character of code."*

`H6` also **confirms the p95 premise for the smaller reason**: at `B = 200` the bias is **−0.026 sd**
against sd **0.146 sd** — **variance beats bias 5.6×** — so D373's 2-SE rule is right and ~18% more
conservative than advertised, and `B ≈ 1,790` buys SE = 0.05 sd. **`[NOT APPLIED]` — amending
standing guidance is the principal's call.**

## R8 · Bar count — the research supplies a test, not a contradiction `[CONFLICT C8]`

`[REPO]` **4,187** bars. `[EXT]` `J6`: **no trade occurred anywhere in US equities on 2012-10-29,
2012-10-30, 2018-12-05 or 2025-01-09.** 4,187 matches the absent case; **4,191 would mean present.**
**The first externally-derived arithmetic prediction about this fixture any round has produced, and
it is two lines to check.** (The `~4,190` `J6` reasoned from was a rounding in a record, not the
measurement.)

## R9 · 1,573 against 1,580 — an internal repo inconsistency, flagged from outside

[FINDINGS §9](../../../FINDINGS.md) records the fixture building out at **1,580 names**; §14, §16 and
§11 measure over **1,573**. Nothing external is in conflict — **research noticed a disagreement
inside our own record.** `[OPEN]`, cheap.

## R10 · The long leg — convergent negatives on different objects, neither tested against the other

`[EXT]` The campaign's central open conflict `F1`: an EW profitability long leg against its own EW
universe is **+0.026%/mo, `t` 0.45** (`C3`) or **+0.405%/mo, `t` 3.00** (`C4`) — both lanes fully
controlled, both stand. `K6`: long-minus-market **Var(t) = 0.98, below the luck null**, so every
post-2005 survivor's long-only return shrinks to **0.00%/month**. And **three separate literatures
do not report the long leg at all** — verified by grep in all three.

`[REPO]` [FINDINGS §28](../../../FINDINGS.md): *"The long excess is cohort membership, not timing: no
long signal beats its own names at random times."*

**Different objects** — a slow annual characteristic tilt versus this programme's fast selectors —
**so this is not a contradiction. Both negatives point the same way and neither has been run on the
other's construction.** Detail: [signals/02](../signals/02-long-leg-versus-short-leg.md).

## R11 · Two cost bars live in this tree and they differ by ~18× — do not carry one across

`shorts/01`–`shorts/05` reason from **1.85 bp/side** on 57 liquid ETFs. The equity campaign reasons
from **33.8 bp/side** on 1,573 dead-inclusive single names. **Both are right about their own
fixture.** Any figure moved between them without re-deriving the hurdle is wrong by more than an
order of magnitude. **Not a conflict — a scope boundary, recorded because the documents sit in one
directory.**

## R12 · The USO/UNG `+733%` bar — an undischarged data-integrity claim `[OPEN]`

`[EXT]` `shorts/02` §4.3: *"the +733% single bar in our USO/UNG fixture is almost certainly a
reverse-split artifact"* — USO executed a 1-for-8 effective 2020-04-29 (an unadjusted +700% bar),
UNG has had multiple 1-for-4s — and *"every result our framework has ever produced touching USO or
UNG is contaminated."*

`[REPO]` **No record mentions USO or UNG.** The *class* is repo truth three times over: the thirty
fabricated dividend days ([§18](../../../FINDINGS.md)), the 15m-versus-daily adjustment split, and the
closed-end-fund composition of `etf_wide_daily_raw` ([§60](../../../FINDINGS.md)). **The specific claim
has never been checked and it is a one-line check.**
