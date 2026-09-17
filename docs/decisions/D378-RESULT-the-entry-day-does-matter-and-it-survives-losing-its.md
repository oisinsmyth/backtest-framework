# D378 RESULT — the entry day does matter, it survives losing its best trade, and it is worth at most half a round trip

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D378-RESULT-the-entry-day-does-matter-and-it-survives-losing-its-best-trade.md`. The H1 above is the full title.*

**Date:** 2026-09-08
**Pre-registration:** [D378](D378-does-the-entry-day-matter-inside-the-cohort.md), committed `b59776e` — **before the runner existed** (R8).
**Runner:** [`scripts/run_d378_entry_day.py`](../../scripts/run_d378_entry_day.py), committed `ad74754`.
**Artifacts:** `data/d378_entry_day.json`, `data/d378_observed.json`, `data/d378_ctrl_p{0..4}.json`.
**Authorised by:** the principal's narrow reopening of 2026-09-08. **Mining prefix only. No holdout was read.**

---

## 0. The verdict — and it is the first clean positive in this sequence

**Both gating hurdles pass, and the prediction I wrote against myself is falsified in the direction
that favours the strategy.**

| | hurdle | verdict | |
|---|---|---|---|
| **T1** | gross mean per trade > A′_c's p95 | **PASS** | +160.55 vs p95 **+144.57** — margin **+15.98 (+26.9 SE)** |
| **T2** | *reported* — the same on the **median** | **FAIL** | +51.55 vs p95 **+64.00** — margin **−12.45** |
| **T3** | **GATE** — T1 with the largest trade removed | **PASS** | **+150.41** vs the same p95 — margin **+5.84 (+9.8 SE)** |
| **T4** | *reported* — horizon profile per bar held | — | the front-loading is **the dip's**, decisively. §3 |

**GATE (T1 and T3): PASS.**

**Q3 was my against-myself prediction that T3 would fail**, because D373's H1 passed and then died on
exactly this test. **It did not fail.** Dropping GME — 2021-01-04, +40,029 bp, 6.34% of the ledger —
leaves **+150.41**, still above A′_c's p95 of +144.57 by 9.8 SE. **The entry-day effect is not one
trade.**

**And it is not most of the book either.** A′_c's centre is **+116.91** of the observed +160.55, so
**73% of the return is still cohort exposure** and FINDINGS §52's level evidence stands. What is new
is that the remaining **~27% is a real, robust, measurable entry-timing effect** rather than the
rounding error §52's corollary called it. §6 amends that.

---

## 1. What was run

**2,000 draws** of A′_c — for each observed signal bar, a replacement drawn without replacement from
the bars on which **that same name** was eligible and in the `mom_252_21` top decile. Five parts × 400,
1.11–1.14 s/draw, ~450 s each.

**The control is built as a SIGNAL grid and fed to the same kernel**, so the fill convention, exits,
slot mechanics and hedge are identical to the observed book by construction.

| the pool | |
|---|---|
| names | 805 |
| pool size per name | min 2 · **median 176** · max 1,226 |
| median pool ÷ entry count | **19.0×** |
| names with pool < entries | **0** — `[DEG]` never close to tripping |
| drawn bars coinciding with an observed entry | p50 **6.45%**, p95 6.83% |

`[POOL]` held on the observed grid and on **every one of the 2,000 draws** — no drawn event ever sat
outside the cohort. `[CNT]` held name by name. `[LAG]` re-derived 400 pool cells from the lagged grid
by a second implementation. In the self-test, a draw from the **full eligible set** — plain A′, the
control this study replaces — correctly **fails** `[POOL]`.

---

## 2. T2 fails, and it says where the gain lives

**The median trade is not better than the control's p95**: +51.55 against +64.00. So the
entry-timing gain is **in the mean, not in the middle** — it comes from the right tail, not from
lifting the typical trade.

**This bears directly on the question that prompted the study.** The principal asked whether better
entry and exit timing could raise per-trade return **and win rate**. The mean answer is yes (T1, T3).
The **median answer is no** — and win rate is the median's neighbour. **Dip timing is not making the
typical trade better; it is making the good trades bigger.**

*(T2 gates nothing by pre-registration, because D374 showed a per-trade median is confounded with
hold length. Here the hold is identical on both sides, so it is informative — and still not
decisive.)*

---

## 3. T4 — the front-loading is the dip's, and both lenses must be read

**Per BAR HELD** — the rate at which the edge accrues:

| cap | observed | A′_c p50 | A′_c p95 | **excess** |
|---:|---:|---:|---:|---:|
| **5** | **7.82** | 2.01 | 4.31 | **+5.82** |
| 10 | 6.86 | 2.69 | 4.23 | +4.18 |
| 20 | 6.12 | 2.81 | 3.87 | +3.31 |
| 40 | 4.02 | 2.93 | 3.62 | +1.09 |
| 60 | 3.94 | 2.75 | 3.33 | +1.19 |

**§52a's proposed mechanism is confirmed.** The observed book's per-bar rate halves from cap 5 to cap
60 while **A′_c's barely moves** (2.01 → 2.75). The decay belongs to **the dip**, not to the cohort:
a randomly-timed cohort entry has no front-loading to lose. At cap 5 the observed earns **3.9× the
control's rate**; at cap 40, **1.37×**.

**Per TRADE** — the same data, the other lens, and it points the other way:

| cap | trades | gross/trade | **excess over A′_c p50** |
|---:|---:|---:|---:|
| 5 | 8,665 | +39.11 | +29.07 |
| 10 | 7,290 | +68.62 | +41.77 |
| 20 | 5,450 | +122.36 | +66.09 |
| 40 | 3,932 | +160.55 | +43.55 |
| **60** | 3,210 | **+235.73** | **+70.95** |

**Both are true and neither may be quoted as the other** (`CLAUDE.md`, FINDINGS §10). The *rate* is
best at short holds; the *accumulated excess per trade* is best at long ones, because a longer hold
collects more bars even at a worse rate. **The per-trade excess peaks at cap 60 — the grid edge — so
under gate 1i it is UNRESOLVED, not concluded**, and cap 20's +66.09 above cap 40's +43.55 makes the
profile non-monotone and noisy.

**The holding period is reported, not picked** (R14, 2026-09-03). Cap 40 remains primary only because
it is D373's cell.

---

## 4. The cost frame, which decides nothing without the spread question

The timing increment is what this study established. **Against a round trip, it is small.**

| cap | excess/trade | ÷ PUB round trip (150.88) | ÷ PB round trip (58.69) |
|---:|---:|---:|---:|
| 5 | +29.07 | 0.19× | 0.50× |
| 10 | +41.77 | 0.28× | 0.71× |
| 20 | +66.09 | 0.44× | **1.13×** |
| 40 | +43.55 | 0.29× | 0.74× |
| 60 | +70.95 | 0.47× | **1.21×** |

**Under PUB the entry-timing increment never funds a single round trip, at any hold.** Under PB it
does, at caps 20 and 60. **Which convention is right is unresolved and is not this study's to
settle** — it is [D336's quoted-spread pull](D336-quoted-spread-validation.md),
which needs the principal's TWS session, and until then every net number here is a PB/PUB pair with
PUB the default (D332 §4).

**So the practical answer to the question that prompted this study is:** *yes, entry timing measurably
improves per-trade return, robustly and by 26.9 SE — and no, it cannot fund a book by itself.* The
construction clears cost only by riding the cohort exposure that §52 retired it for.

**And a caution the pre-registration recorded in advance:** a shorter hold raises the per-bar rate and
raises the number of round trips paid. **Which moved is stated above** — the rate rose, the cost per
unit of exposure rose with it, and cost-cutting is not edge-sharpening.

---

## 5. Predictions, scored

| | prediction | outcome |
|---|---|---|
| **Q1** | A′_c's p50 in +100 to +140 | **HELD** — +116.91 |
| **Q2** | T1 passes, margin under 20 bp | **HELD** — +15.98 |
| **Q3** | *against myself:* **T3 fails** | **FALSIFIED** — it passed at +9.8 SE. **The one I most wanted to be wrong about, and was** |
| **Q4** | the observed decays faster than A′_c | **HELD** — decisively (§3) |
| **Q5** | median pool > 100 bars | **HELD** — 176 |
| **Q6** | under 5% of drawn bars coincide with an observed entry | **FALSIFIED** — 6.45%. Flagged in the runner's commit before the run, from a single-draw 6.32% |
| **Q7** | A′_c's centre between A′'s +59.42 and the observed +160.55 — **a validity rail** | **HELD** — +116.91, and close to `B_c`'s +126.54 as reasoned |

**Five held, two falsified — and for the first time the falsification favours the strategy.** Q7 was
the rail that would have voided the study if the pool were mis-specified; it held, and A′_c landing
near `B_c`'s independently-measured centre is corroboration from a different construction.

---

## 6. What this changes, and what it does not

**FINDINGS §52's level evidence stands unchanged.** A′_c's +116.91 of +160.55 is a **third**
independent measurement that most of the return is cohort: 73% here, against D373's `B_c` at 79% and
D377's hedge at 79%. **Three controls, three constructions, the same answer.**

**§52's COROLLARY is too strong and is amended.** It said the selector is *"a rounding error on a
factor exposure."* It is not: the increment is **+15.98 bp per trade at 26.9 SE**, it **survives
leave-one-out at 9.8 SE**, and its per-bar rate is **3.9× the control's at short holds**. **A real
effect that is small relative to cost is not a rounding error — it is a small real effect, and the
two must not be written as the same thing.**

**The reopening's abandon condition did NOT fire.** §8 of the pre-registration said: *"T1 fails
outright → §52's retirement stands as written, this reopening expires."* **T1 passed and T3 passed.**
So the retirement does not automatically stand — **and nor does the avenue automatically reopen.
Under R15 that is the principal's call, and this record does not presume it.**

**What the principal now has that they did not before:** the effect is real and robust; it is ~27% of
the book; it is worth at most 0.47× a round trip under PUB and up to 1.21× under PB; and **which of
those is true depends on a measurement nobody has taken.**

---

## 7. What this did not settle

- **Exit timing.** Excluded by pre-registration §2, and [R7](../RULES.md#r7) says why: a rule that
  modifies an existing book needs a **matched-count random-exit** control, not a rotation. D235
  cleared a rotation null at p95 −0.284 and then landed at the **63rd percentile** against the right
  one. **Still owed, still a separate pre-registration, and not authorised by this reopening.**
- **Whether a shorter hold is deployable.** T4 says the rate is better there and §4 says cost is
  worse. The per-trade excess peaks at the **grid edge**, so gate 1i marks it unresolved.
- **The spread convention.** §4 — D336, and it needs the principal's session.
- **Anything out of sample.** Neither fixture was read. Holdout #2 remains unspent.
- **Whether this generalises past D373's cell.** One cell, inherited, one cohort definition.

---

*Result committed separately from the pre-registration, per R8. Nothing admitted to either book; the
prop book remains empty. One look added to the winners'-dip ledger, disclosed, on a fixture already
spent.*
