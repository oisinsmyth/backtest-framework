# D460 RESULT — conditional exits are the FIRST thing in this chain to beat a matched control, and they still fail P4 by fourfold

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D460-RESULT-conditional-exits-are-the-first-thing-in-the-chain-to-beat-a-matched-control-and-they-still-fail-P4.md`. The H1 above is the full title.*

**MEASUREMENT record. No hurdle is claimed and no candidate is admitted.** Closes
[D459](D459-RESULT-beyond-22-hours-the-shape-constraints-lever-does-not.md)
§5's last open object. **Runner:** `scripts/d460_conditional_exits.py`. **Fixture:**
`data/fixtures/es_stop_grid.csv.gz` (3,584 holds). **Evidence:**
`data/d460_conditional_exits.json`. **E2 was wrong, and it is the only interesting thing here.**

---

## THE ANSWER

> **Five of ten stop cells clear their time-matched control's p95, three of them at `p` = 0.000 on
> 60 draws — the first construction in this entire prop chain to beat a control.**
>
> **And not one of them clears P4. The best funded life is 0.87 years against three.**

## 1. Why a stop was worth testing at all, against this repo's own prior

**`FINDINGS` §5 records that exit overlays have a measured ceiling on this book.** D380: no exit
overlay beats a random cut. D394: no exit rule closes the gap and the take-profit inverts.
D423–D425: every structure exit forfeits.

**All of those score RETURN. A prop account does not.** Under [R11's ruling](../RULES.md#r11) P4 is
the **account's life**, and **an exit that costs return can still raise `V` if it raises survival by
more.** That asymmetry is the only reason this is not a repeat — and it is the same asymmetry `O1`
was screened on.

**Two rules, differing in exactly the way the floor does:**

```
FIXED      exit when price <= entry x (1 - s)         caps MAE from ENTRY
TRAILING   exit when price <= running peak x (1 - s)  caps drawdown from the PEAK -- the MLL's
                                                      own logic, applied inside the hold
```

## 2. The result

| rule | `s` | hit% | mean bp | p99 MAE | **`V`** | funded yr | ctrl p50 | ctrl p95 | `p` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| *BASE* | – | – | 5.33 | 3.39% | *92* | *0.27* | – | – | – |
| fixed | 0.5% | 46.0% | 1.86 | 0.89% | 299 | 0.23 | 270 | 675 | 0.367 |
| **fixed** | **1.0%** | 20.7% | 4.61 | 1.17% | **1,470** | **0.87** | 193 | 514 | **0.000** |
| **fixed** | **1.5%** | 10.9% | 4.43 | 1.62% | **736** | 0.59 | 155 | 406 | **0.000** |
| **fixed** | **2.0%** | 5.7% | 4.38 | 2.10% | **687** | 0.41 | 137 | 304 | **0.000** |
| fixed | 3.0% | 1.8% | 4.93 | 3.04% | 112 | 0.13 | 125 | 248 | 0.650 |
| trailing | 0.5% | 74.9% | 1.75 | 0.73% | 227 | 0.46 | 281 | 825 | 0.567 |
| trailing | 1.0% | 36.6% | 3.40 | 1.08% | 543 | 0.50 | 186 | 605 | 0.100 |
| **trailing** | **1.5%** | 18.8% | 4.07 | 1.51% | **534** | 0.59 | 162 | 474 | **0.017** |
| **trailing** | **2.0%** | 10.5% | 3.74 | 1.98% | **750** | 0.55 | 186 | 396 | **0.000** |
| trailing | 3.0% | 3.8% | 3.72 | 2.84% | 221 | 0.26 | 119 | 241 | 0.100 |

**The clearing cells are a CONTIGUOUS BAND — fixed 1.0–2.0% and trailing 1.5–2.0% — not scattered
singletons.** That is the shape a real effect has and the shape noise usually does not, and it is
the reason this is reported as a finding rather than as five lucky cells out of ten.

## 3. The control, and the two versions of it I had to write

**A stop mechanically shortens the hold and truncates the left tail, so ANY stop improves survival
for reasons that have nothing to do with state.** The control is therefore a **time-matched random
exit**: the treatment's own exit times, permuted across holds, with each hold exited at the price
that actually obtained at its assigned time.

> **THE FIRST VERSION OF THAT CONTROL WAS BROKEN AND I CAUGHT IT BEFORE REPORTING.** It synthesised
> the exit as `base_end × frac` — a proportional share of the hold's final return. **A stop
> TRUNCATES a loss; a proportional share cannot.** The control could never truncate and the
> treatment always could, an asymmetry with nothing to do with state-dependence that on its own
> would have produced the result. **Rebuilt on 20 real-path checkpoints per hold.**

> **AND A SINGLE CONTROL DRAW IS NOT A NULL.** The first corrected run compared each cell to **one**
> permutation and reported "8 of 10 beat their control." **D442 enumerated 3,265 rotations.** The
> time-matched exit has no finite group to enumerate, so it is sampled — **60 draws per cell**, and
> the treatment is compared to a **distribution**. That took it from 8 of 10 to **5 of 10**.

**Both corrections moved the answer, and both were made before anything was written down.**

## 4. What it does not do

- **`E4`: no cell clears P4's three years.** Best is **0.87 years**, a fourfold miss, and that is the
  bar the [R11 ruling](../RULES.md#r11) made operative.
- **In-sample throughout, no holdout**, like everything else in this chain.
- **Ten cells were tested and five reported.** They are adjacent levels of two related rules, so the
  effective number of independent tests is well below ten — **but it is above one, and no
  multiplicity correction is applied here.**
- **The fill is optimistic**: a triggered stop fills **at the stop level**. The measured overshoot —
  how far past the stop the triggering bar's low actually went — is **1.42 bp on average**, which
  bounds the optimism and is small relative to the 100–200 bp stop levels themselves.

## 5. Predictions

| | prediction | outcome |
|---|---|---|
| **E1** | every stop raises funded life and lowers mean return | **PARTLY** — mean return falls everywhere, but funded life **falls** at fixed 0.5% (0.23 vs 0.27) and fixed 3.0% (0.13) |
| **E2** | **no** cell beats its time-matched control | **WRONG, and it is the finding** — five clear the p95, three at `p` = 0.000 |
| **E3** | trailing beats fixed on funded life at matched level | **PARTLY** — true at 0.5%, 2.0% and 3.0%; false at 1.0%; tied at 1.5% |
| **E4** | no cell clears P4 | **CONFIRMED** — best 0.87 years |

**E2 is the first prediction in this chain I have been wrong about in the optimistic direction.**
Every other miss this session made something look worse than I expected; this one makes something
look better, and it survived two control rebuilds that were each designed to kill it.

## 6. What this means, stated carefully

**This is a signal, not a candidate.** Under [R15](../RULES.md#r15) a signal is a positive gross
mean above its nulls, and **a conditional exit on C1 now has one** — the first in the prop chain.

**It is also a NEW MECHANISM**, which is exactly what
[D459](D459-RESULT-beyond-22-hours-the-shape-constraints-lever-does-not.md)
§5 said a fifth candidate would need. **Hold length chosen by the market beats hold length chosen by
a clock, and the clock sweeps in D458 and D459 found nothing precisely because they were clocks.**

**But it does not rescue C1 and nothing here says otherwise.** P4 is missed fourfold by the best
cell, and P4 is the account's life.

## 7. What it leaves

1. **A pre-registered test with a holdout.** Everything above is in-sample on one construction, one
   instrument, one venue. **The band is contiguous, which is the reason to spend a holdout on it
   rather than to believe it.**
2. **Multiplicity, properly.** The right null for "the best of ten stop cells" is a control
   distribution of the **max over all ten**, which is not what §2 reports.
3. **The interaction with sizing.** Every cell here re-optimises the risk fraction, so a stop is
   competing with de-sizing rather than combining with it. **Whether a stop adds anything to a book
   already sized down is untested.**
