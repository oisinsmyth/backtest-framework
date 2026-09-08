# D392 — the base-rate atlas: what a random event set of size *n* earns on this universe, and its p95

**Status:** SPEC, PRE-REGISTERED. Committed **before the runner exists** (R8). **Nothing here is a
result.**
**Date:** 2026-09-08 · **Area:** infrastructure / measurement · **personal track**

**Standing: a MEASUREMENT record, [D280](D280-the-forecast-precheck.md)'s class.** It scores no
cell, ranks no name, proposes no rule and **admits nothing (R15). Ledger contribution: 0.** It runs
*before* there is anything to pre-register, because it decides what a later pre-registration's
numbers mean.

**Holdout reads spent: 0. Programme total: 1** (D371). The holdout is not touched.

**Build (R16):** today's panel, `load_ragged(dividend_bound=True)`. Every number in the atlas is
stamped with the panel, the fixture, the floor (`keep_v2`), the F0 filter and the kernel version,
because an atlas quoted years from now against a moved pipeline is worse than none.

**Number.** D390–D399 is reserved for this branch (`e5c9189`); master took D380–D382 while this
work was in flight.

---

## 0. Why this exists — five failures with one shape

Five candidates died on 2026-09-07/08 and **not one of them died on cost:**

| | what actually earned the number |
|---|---|
| C1 dispersion | volatility (ρ 0.774) |
| C1 breadth | G1 restated (ρ 0.658) |
| C2 the fade's gate | a random gate of the same shape, to within **+0.52 bp** |
| [D390](D390-RESULT-zr-is-the-whole-tilt-and-its-tail-goes-the-wrong-way.md) `zr` | the whole cross-section — a negative rank IC with **both tails rising** |
| [D391](D391-RESULT-the-reclaim-is-worth-less-than-no-reclaim-and-the-edge-was-the-event-bar.md) undercut-reclaim | the pool and the hold — the long paid **+43.02** and its own **mirror paid +43.73** |

**Each rediscovered a base rate at the price of a full pre-registration.** D391's mirror is the
cleanest statement of the problem: two opposite constructions on opposite signals earned the same
thing, and nothing in the programme said in advance what "the same thing" was.

**[D376](D376-RESULT-two-unrelated-books-here-correlate-at-0.48-and-two-cohort-books-at-0.92.md) is
the template.** It measured the structural correlation floor once — **+0.48** for unrelated books,
**+0.92** for cohort books — and every correlation claim since is readable against it. **There is
no equivalent for the per-trade mean, which is the statistic R15 gates on.**

---

## 1. The statistic

**Gross mean per trade, in bp**, from the same kernel every study uses (`EB.simulate_event` through
`run_d359`'s `run_mirror` / `run_short`), same next-open fill (D340), same floored hedge, no cost.

**Reported as a DISTRIBUTION, never a point:** p05, p50, **p95**, max, and **the bootstrap SE of the
p95**.

---

## 2. The grid

| axis | values | why it must be an axis |
|---|---|---|
| **event count** *n* | 100, 300, 1,000, 3,000, 10,000, 30,000, 60,000 | the p95 shrinks with *n*; D391 had 61,835 trades and the record had no idea what that was worth |
| **hold** (cap) | 5, 10, 20, 40, 60 | per-trade mean is **monotone in hold** — [D289's seventh amendment](D289-the-promotion-pipeline.md). One number would be meaningless |
| **side** | long, short | D391's mirror earned +43.73 against the long's +43.02. Both sides need a floor |

**7 × 5 × 2 = 70 cells, each a distribution.** **500 draws per cell** — the principal's ruling,
2026-09-08.

### 2a. The conditional table, which is the part that earns its keep

Unconditional floors would have caught D391 and **missed** dispersion and `zr`, because **every
real candidate selects on something.** So the atlas also draws from **conditioned pools**, at the
primary cap (20) and *n* ∈ {3,000, 10,000, 30,000}, both sides, **200 draws**:

- **price tercile** (the axis that killed D284)
- **volatility tercile** (the axis that killed C1 and D390)
- **momentum tercile** (the axis that killed D373 and produced FINDINGS §52)

**This makes §52's rule mechanical**: a candidate holding high-volatility names is compared to
*random high-volatility names*, not to the universe.

### 2b. A concentration sensitivity, reported and not a full axis

A candidate firing on 50 names is not a candidate firing on 700 (D371: 2 of 255 names to half the
P&L). At cap 20 and *n* = 10,000, the atlas additionally draws events spread over **all eligible
names / 25% of them / 5% of them** and reports the three floors. **Concentration is a reported
sensitivity in v1, not a full axis** — it multiplies the grid and the three levels answer the
question a reader actually has.

---

## 3. What "random" means — the load-bearing design decision

**This is where the record can go wrong, and the programme has already paid for the lesson.**

> **[D291]: a random subset is never a control for a persistent selector — it re-draws each bar, so
> it churns.** 2.4× the entries, up to 7×, which voided 87 cells.
> **A control must share the treatment's nuisance, not just its count.**

**So:**

1. **The draw is over eligible (name, bar) cells**, satisfying the same `elig` mask observed events
   must satisfy (D351), and **never** the excluded tail — D339 found those bars earn +226 to +318 bp
   and D347's control A was broken by exactly that.
2. **Events are placed, then held by the kernel** — one position per name at a time, next-open
   fill, cap exit. **The atlas therefore measures trades, not events**, and reports both counts, as
   D391 found: 144,657 events collapsed to 61,835 trades.
3. **The primary draw is UNIFORM over eligible cells**, which is the honest "no information" null
   for an unknown future candidate. §2b's concentration levels cover the case where a candidate's
   events are not spread that way.
4. **The kernel is the studies' own.** A new sampler would make the atlas incomparable to the
   studies it exists to serve — `assert_matches_scorer`'s entire point.

**What the atlas is NOT:** it is not `A′`. `A′` rotates a *specific* candidate's observed events
and stays the right control for that candidate. **The atlas is the prior a candidate is read
against before it has earned a null run** — a triage instrument, not a replacement for one.

---

## 4. The atlas obeys its own rules

- **Its p95 is a SAMPLED quantile, so C2b's bias applies to the atlas itself** — biased toward the
  centre, hence **too lenient**. Every entry carries its bootstrap SE, and **this null is not a
  finite group**, so C2b's enumeration remedy is unavailable and draw count is the only lever. That
  is why 500 was chosen over 200 for the main table.
- **Every entry is stamped with its build** (R16).
- **It admits nothing** (R15).

---

## 5. The deliverable

`data/d392_atlas.json` **plus a small importable lookup**, so future runners *call* it rather than
a reader admiring a table:

```
atlas.floor(n, cap, side, pool=None)  ->  {p50, p95, se_p95, draws, n_grid_used, interpolated}
```

- **Interpolates in `n`** (log-linear between grid points) and **says so in the returned dict**; it
  never silently extrapolates beyond the grid — outside it, the call raises.
- **A candidate quoting the atlas states the pool it used.** A raw floor quoted without its pool is
  the same error D376 found in gate 1d.

---

## 6. Assertions the runner must carry

- **[E]** every drawn event sits on an eligible bar — the same mask observed events satisfy
  (D351) — and the share that would not have is reported as 0.
- **[K]** the kernel is the studies' own: a hand-placed event set scored through this runner equals
  the same set scored through `run_d359`'s path, to 0.0.
- **[N]** the trade count is reported beside the event count at every cell; a cell whose collapse
  ratio differs wildly from its neighbours is flagged, not averaged away.
- **[SE]** the bootstrap SE of every p95 is computed and stored; no p95 is written without one.
- **[P]** the JSON is persisted **before** anything is rendered, and **incrementally per cell** —
  a 4-hour run that dies in a print loop must not lose 70 cells. *(D371 lost its evidence that way;
  D391's runner reproduced the same defect earlier today and this one is written against it.)*
- **[X]** the self-test **RAISES** on (a) a draw placed on an ineligible bar and (b) a p95 written
  without its SE.

---

## 7. Predictions

Committed before the runner exists. **Q1 is load-bearing** and is the one that would retroactively
settle D391.

| | prediction |
|---|---|
| **Q1** | *(load-bearing)* the **long** p95 at cap 20, *n* = 60,000 is **within ±15 bp of +43** — i.e. D391's ledger sat at or below its own floor, and its "base rate not signal" reading is confirmed by an instrument built after the fact |
| **Q2** | the long and short floors at the same (n, cap) differ by **less than 15 bp** — D391's +43.02 vs +43.73 was not a coincidence |
| **Q3** | the p95 scales approximately as **1/√n**: the ratio p95(1,000)/p95(10,000) lands between 2 and 4 |
| **Q4** | the floors are **substantially positive at every cap**, and rise with cap — the next-open fill credits the entry gap (FINDINGS §21: *worth more than the spread*) and a longer hold accumulates drift |
| **Q5** | the **volatility tercile** spread in the conditional table is the largest of the three axes — larger than price or momentum |
| **Q6** | *(against)* the concentration levels of §2b differ by **more than 25 bp** at 5% of names versus all names, i.e. concentration matters enough that v1's decision to make it a sensitivity rather than an axis is the wrong call and v2 should promote it |

---

## 8. Cost, and what is deferred

| | runs | draws |
|---|--:|--:|
| unconditional | 70 cells | **500** |
| conditional | 9 pools × 3 counts × 2 sides = 54 cells | **200** |
| concentration | 3 cells | 200 |
| **total** | ~127 cells | **~46,000 kernel runs** |

**Estimated 4–6 hours in the background**, on a measured basis of 0.1–0.15 s/draw (D362 timed this
kernel at 0.118 s; C2's runs came in near 0.1 s on 4–9k trades). **The 30k and 60k cells dominate**
and are run last, so a partial atlas is still useful — `[P]`'s incremental write is what makes that
true.

**Deferred to v2, and named so they are not silently dropped:** sector splits, dead-vs-alive,
era, the intraday fixtures, and promoting concentration to a full axis (Q6 may force this).

---

## 9. What would make me abandon this

- **[K] fails** — this runner's kernel is not the studies' kernel, and the atlas would be
  incomparable to everything it exists to serve. **Fix or stop; do not publish a floor from a
  different kernel.**
- **The floors are so wide they discriminate nothing** — if p95 at *n* = 60,000 is within a few bp
  of p95 at *n* = 1,000, the statistic is not concentrating and the atlas has no resolving power.
  **Record it as a finding about the statistic** — that would itself explain a great deal about
  this programme's history — and stop.

---

**Status footer.** No runner exists. `docs/BOOK.md` holds S1 and S2, neither at capital;
`docs/BOOK_PROP.md` is empty. This record proposes no strategy and closes no avenue (R15).
