# The stack, signal to present

**What each layer contributes, what it is worth once costed honestly, and where
the next study goes.** Rewritten 2026-09-05 after D322–D330. The previous
version stopped at D321.

Companion to [FINDINGS.md](FINDINGS.md) (substantive results) and
[decisions/](decisions/README.md) (one call each).
**[PICKUP.md](../PICKUP.md) is stale** — last updated 2026-09-02.

**§7 records what earlier versions of this document got wrong.** It has grown.

---

## 0. The stack, and what it earns — now stated as BOUNDS

```
signal        hist_L primary, D293 confluence      the LONG leg is real; the SHORT leg is
                                                   the worst leg measured (D329), for a
                                                   SIZING reason (D328 §11)
construction  factor-neutral spread                removes -mu - sigma^2                  (D285)
width         N_eff = 2, FIXED                     +21 bp over N=19, basis-immune       (D300)
exit          the target, or nothing               +0.69 bp/bar, and only at N <= 3
overlay       CLOSED at this width                 negative at all 12 thresholds        (D319)
tilt          CLOSED, one variant carried          dv28, p = 0.0100, unconfirmed        (D320/D321)
```

**The incumbent book, under BOTH spread conventions** (D332). `PB` is the
per-bar median the programme has used since D318; `PUB` is the estimator as
its authors specify it, a trailing 21-bar mean. IBKR per-share commission in
both. **PUB is the default until quoted spreads decide** (D332 §4).

| N=2 / target, k=5 | net bp/bar | net Sharpe | held ½-spread |
|---|--:|--:|--:|
| **PB** (D321's costing) | +14.57 | +0.334 | 18.3 |
| **PUB** | **−5.16** | **−0.118** | 38.8 |
| PB, D318's costing | +11.36 | +0.261 | 18.3 |

**Under the published convention the incumbent loses money.** Its short leg
alone nets −180.8 bp per trade. What survives the swap is every *relative*
finding — concentration (+32 bp N2−N19), the leg-wise construction, the D323
order — and one absolute one: **`retrace_leg` at k=20, +16.06 bp/bar and
Sharpe +0.480 under PUB, is the best symmetric book in the programme under
either convention.**

**Every net number in this document is an UPPER BOUND even under PUB.** §3
lists the holes that remain — borrow and rebalancing — each with a measured
mechanism.

### The best construction the programme has, and its bound

**Leg-wise: `hist_L` picks the longs, `skew_63` picks the shorts** (D329). No
composite before it let two signals own one leg each. It composes exactly —
its long ledger *is* `hist_L`'s and its short ledger *is* `skew_63`'s,
bit-identically in both lenses — so what it adds is the pairing, not a new
signal.

| k=20 | net per trade, PB | **net per trade, PUB** | net Sharpe, PB | net bp/bar, PUB |
|---|--:|--:|--:|--:|
| `hist_L` symmetric | −0.89 | −59.39 | −0.082 | −18.58 |
| `skew_63` symmetric | +44.83 | +8.14 | +0.421 | +4.97 |
| **leg-wise** | **+51 to +63** | **+17 to +36** | +0.22 to +0.43 | −4.0 to +5.6 |

*The range on each leg-wise cell is the D330 filter bound (over-filtered to
deal-contaminated). Under PUB the leg-wise book is a +36 per-trade edge and a
roughly break-even bp/bar book; it still beats both parents in both.*

**The number is a bound because a fifth of `skew_63`'s short trades are
takeover targets pinned at the deal price** (D329 §10, D330): the short earns
nothing on them, cannot borrow them, and the spread estimator reads them as
nearly free. The low end is over-filtered, the high end is contaminated, and
at either end it beats both parents. `skew_63` is **first of 44** short
partners for `hist_L`-long on both lenses; `hist_L` is **fourteenth of 45**
long partners for `skew_63`-short — **the short leg is settled, the long leg is
not.**

**Status: a construction, not a candidate.** Nothing clears R8. Book: empty.

### The one declared VARIANT, carried and not promoted

```
+ dv28   exclude the bottom 28% of the live cross-section by trailing
         dollar volume, per bar, on a lagged 63-day mean          (D321)
```

| | gross | cost | **NET** | **netSHRP** | held ½s | held price |
|---|--:|--:|--:|--:|--:|--:|
| base (`N=2/target`, D321's costing) | +32.89 | 18.33 | +14.57 | +0.334 | 18.31 | $71 |
| **base + dv28** | **+32.93** | **14.56** | **+18.37** | **+0.507** | 14.54 | $73 |

**Status: CARRIED, NOT PROMOTED. p = 0.0100 against its rotation null**, clears
BH at every plausible effective count, misses at the nominal 19, unconfirmed on
a separate construction. **Any study using dv28 reports the cell with AND
without it.** It does not enter [BOOK.md](BOOK.md).

## 1. Three axes — unchanged, and still closed

### Axis A — should width VARY over time? **No. Five studies, all closed.**

D299, D308, D311, D312, D313. **D314 explains all five at once**: with
ρ = 0.0020, `Sharpe = √N·net/σ`, net is monotone down in width, so the optimum
is a **corner**, and a rule that varies N can only move away from one.

### Axis B — which FIXED width? **N_eff = 2, basis-immune.**

In D300/D306's construction turnover is `1/k` at every depth, so the cost basis
cancels: **concentration wins by ~21 bp whatever round trip is charged.**

### Axis C — which CONSTRUCTION? **D300/D306's, not D310's.**

D310 turned over 1.73× more and its width result flipped sign under the correct
basis (D317). D311–D316's *relative* results survive; their absolute nets do not.

## 2. The exit work — unchanged

Target +4.95 bp/bar, p = 0.0050 (D295); trailing overlay p = 0.0150 at N=19 and
**negative at every threshold at N=2** (D319). Costed correctly the target is
worth **+0.69 bp/bar at N=2**, reproduced three ways (D305, D307, D318). Stops,
displacement, idle conditions, the ladder: dead. `sel = rank < N_SLOTS` pins the
family: a price exit beside a signal exit is arithmetically inert.

## 3. Cost — wrong twice, fixed twice, and now open in three places

**Fixed (D317, D318):** the spread basis — per-cell across widths, common
within a width — and commission, which was never charged before D318.

**What the cost model charges today:** `4 × held median Corwin–Schultz
half-spread` per paired round trip, plus IBKR's official per-share commission
`$0.005 / price` per crossing. **The commission is IBKR's published schedule
and is not in question** — except that the schedule's **$1.00 per-order
minimum and 1% of trade value maximum are not applied**; the minimum depends on
position size and is the PM's to add, the maximum binds only below ~$0.50.

**Open, each with a mechanism:**

| hole | mechanism | size | status |
|---|---|---|---|
| **The spread CONVENTION** | The per-bar Corwin–Schultz estimate is clamped to zero on **43%** of live name-bars, uniformly, uncorrelated bar to bar; PB takes the median of that coin flip at entry, so a leg above 50% zeros is charged nothing. The authors average daily estimates over a month (`cs_spread`), which reads **2.03×** PB at the median across legs | incumbent +14.57 → **−5.16** bp/bar; every net level falls 8–20 bp/bar; relative findings unchanged | **D332. PUB is the default; which is TRUE needs quoted spreads (Part C, on IBKR)** |
| **No borrow cost** | Announced deal targets are the most crowded short in the market; any post-jump name may be hard to borrow. PUB does not touch this — a pinned deal stock's *spread* really is tiny; its cost is borrow | unquantified; the fixture has no borrow data. Deal dates now exist (D331) | open |
| **Daily rebalancing is uncosted** | The book is equal-weight, rebalanced daily, and earns the *sum* of one-bar returns; the trades that realise that sum are free. On `hist_L`'s $8–10 names, ~5%/day of notional at 46.7 bp | ~30 bp/name/hold against a `two_c` of 96 | open, D328 §11 |

*The "floor at zero" hole the previous version listed was a symptom of the
convention, not a hole of its own: under PUB the half-tick floor moves nothing
by more than 1 bp (D332 Q7).*

**And one that is not a cost but decides which leg pays it — the rebalancing
premium.** A rebalanced long on a bouncy name harvests volatility; a rebalanced
short pays it. On `hist_L`'s names that is **+23.5 bp per trade to the long leg
and −45.9 to the short**, and it is why the incumbent's short leg nets **−98.4
per trade** — a sizing artefact with a concrete fix (constant shares), not a
signal failure (D328 §11, D329 §2).

## 4. What is decisive, and what is merely not-rejected

**Decisive against a null:** the spread construction; concentration
(p = 0.0050 at every depth); **leg ownership on the short side** —
`skew_63` first of 44 real partners, above the control's p95, on both lenses
(D329).

**Real but small, confirmed three ways:** the target, ~+0.7 bp/bar.

**Real, and now with a mechanism:** `hist_L`'s long leg (+97 net per trade,
t ≈ 3, **decays by k=40** as a real signal should); the two-leg asymmetry.

**Not resolvable on this fixture:** any per-bar paired test at N_eff = 2 — MDE
11–18 bp/bar against a book netting ~11 (D316). Any per-trade `t` on a leg
that lives in its tails — `skew_63`'s short leg is +0.9, with its top 1% of
trades at 159% of P&L and its bottom 1% at −203%.

## 5. What happened between D322 and D330, in one paragraph each

**D322 — the four-group report.** 57% of the incumbent's P&L sits in the
cheapest price tercile at 8× the commission. Cost scales as 1/price; the book
is a cheap-name book.

**D323 / D324 — the shortlist at the operating point.** D290's 51 re-read at
N=2. `retrace_leg` (+20.91 bp/bar, netSHRP +0.625 at k=20) and `rsi` (+22.66,
+0.585 at k=10) lead the incumbent's +11.36. **The ranking inverts with width**
and the incumbent is the least fragile of the four. A defect in the short leg's
rank order — it shorted the *least* extreme names — was caught by a later
assertion and voided the first run.

**D325 / D326 — composites, both lenses.** D325's +0.370 composite premium and
a −0.644 pair effect. **D326 split them: the premium was the slot cap
re-ordering which two names survive; the pair effect is a signal effect and
survives the cap removed.** Neither beats `retrace_leg` alone. The mechanism
D327 offered for the pair effect was withdrawn (below).

**D327 / D328 — the rank profile, at two resolutions.** No signal is monotone;
the edge is a tail effect with a noisy middle. **`macd_hist` is computed in
dollars and its extreme ranks are a price sort** — $2,706 at one end, $3,020 at
the other, $22 in the middle — with a compounded spread of +18 bp carrying
146 bp of cost. Three of D290's 51 carry dollars by accident. D328 was
corrected three times in one day: a summed-vs-compounded *convention* mistaken
for an error, a persistence hypothesis filed unmeasured, and a price-deviation
"result" that was both errors stacked. What survived is the rebalancing
premium and the tilt mechanism: **return cancels between the legs, cost adds
across them.**

**D329 — the leg-wise composite.** §0 above. Six of seven predictions failed
as written (every-k forms, a +0.10 margin); the substance at the operating
point held; the enumeration was the finding.

**D330 — the pinned names, mapped, and the tape's limit.** Short side: median
1.5% pinned, `skew_63` 21%, `hist_L` 1.2%. Long side: **every volatility score
24–35%**, surviving names at half-spread 0.0 — axis E's long side was never a
book. A causal filter caught 71% of pinned trades and removed 39% of survivors:
**a jump followed by quiet is a deal and a reversal candidate alike.** A
deal-event source is required; an EDGAR pull is in progress (D331).

## 6. Next, in order, and why the order

**The next four studies are infrastructure. Another signal result now is
another upper bound on a cost model known to be wrong in three places.**

1. **Deal events — DATA PULLED (D331).** 1,465 of 1,573 names resolved,
   24,387 filings, 1,053 target-specific forms. **The study that uses it is
   next**: an event-driven exclusion on `skew_63`'s short leg, validated
   against D330 A's pinned labels (the test D330 B's tape filter failed), with
   the role ambiguity of form 425 declared.
2. **The spread convention — DONE (D332).** The floor was the wrong study;
   the convention was the finding. **What remains is Part C**: quoted BID_ASK
   bars from the principal's IBKR session on a stratified sample of live
   names, to decide PB vs PUB vs Abdi–Ranaldo. A data task, not a study I can
   run.
3. **Constant-shares sizing on the short leg.** The direct test of the
   rebalancing mechanism, and if it holds it rescues the incumbent's short leg
   rather than dropping it.
4. **A borrow stress charge**, declared, since no borrow data exists — now
   with deal dates to anchor the highest-rate cohort.

**Then, signal-side, each with a mechanism behind it:** the long leg for the
leg-wise book, chosen from the profile side and *predicted* (the enumeration's
winner is post-hoc and does not count); `macd_hist` normalised and D325 re-run;
collapse capture in the high-vol short legs — 0–4% of trades at +1,300 to
+3,500 each — which needs a tail-aware framework, not a mean per trade.

**Owed, still:** sub-2 widths on D300/D306's construction (D315a tested them on
D310's); D318's re-costing detaches D300/D306's null p-values from their exit
cells; dv28 on a separate construction at a threshold fixed at 28.

## 7. What earlier versions of this document got wrong

Kept legible rather than quietly fixed.

1. **"Nothing after D300 was an improvement."** Wrong — D303, D305 arm S, D306.
2. **Calling the target and the exits "decoration" on a paired t of +0.17.**
   Wrong bar and wrong inference: the programme's standard is beating your own
   matched null, and the paired test was blind (MDE 18 against a book netting 11).
3. **Quoting D310's `none/exp2` at +4.37 as "the best cell".** Wrong
   construction and the universe's cost basis.
4. **"Cost, which was wrong twice and is now right."** *(the previous
   version's §3 heading)* It was wrong in three further places, each large
   enough to move a verdict, and the sentence was written the day before the
   first of them was found. **A cost model is never "now right"; it is "not yet
   found wrong in these places."**
5. **The composite mechanism** — "a signal can carry information at depths its
   own book never trades." Filed after the effect it explained, on a signal
   that turned out to rank price. Withdrawn.
6. **Three corrections on one study (D328).** A convention called an error; a
   hypothesis filed before it was measured; a perfect Spearman on five points
   with a measure chosen after seeing them. All caught before promotion, two by
   the principal's questions and one by a read-only audit agent.
7. **The best cost coverage in the programme (`skew_63`, 4.5×) was
   "unexplained" for three studies.** It was takeover targets read as free.
   **Measure the price and the spread of what each leg HOLDS** — FINDINGS §14
   — would have found it in D326.

The common thread has not changed: reading a non-result as a null result,
ranking cells off a published table instead of measuring the difference, and
filing a mechanism before checking the statistic orders the outcome.
