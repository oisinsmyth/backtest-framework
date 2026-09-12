# D459 RESULT — beyond 22 hours: hold length barely moves DAILY risk, so the shape constraint's lever does not exist at the frequency the rules operate on

**MEASUREMENT record. No hurdle is claimed and no candidate is admitted.** Closes
[D458](D458-RESULT-the-hold-length-curve-has-no-identifiable-optimum-and-the-observed-argmax-is-below-its-own-nulls-MEDIAN.md)
§7 item 1 — the range the prop research's shape constraint actually points at. **Runner:**
`scripts/d459_multiday_holds.py`. **Fixture:** `data/fixtures/es_daily_marks.csv.gz` (2,539 daily
marks). **Evidence:** `data/d459_multiday_holds.json`.

---

## THE ANSWER

> **A 20-day hold has the same DAILY risk as a 1-day hold. Daily sd moves 1.042% → 1.065% across a
> twentyfold change in hold length; p99 MAE 3.376% → 3.707%; the 1× breach rate 1.694% → 1.772%.**
>
> **The shape constraint's lever — "longer windows carry more σ per contract, so fewer contracts,
> so less pressure on the floor" — DOES NOT EXIST once the position is marked daily against a
> floor that ratchets daily and a qualifying threshold that is also daily.**

**And, as in D458, there is no identifiable optimum: the observed argmax of 198 sits far inside its
own null, `P(null ≥ observed) = 0.883`.**

## 1. D458's obstacle dissolves, and it was my over-caution

D458 §7 left this untested because *"a multi-day hold ratchets the floor at each EOD while the
position stays open, which D440's lifecycle cannot express without a modelling assumption."*

**That was wrong. D440's loop already marks to market daily** — it consumes one `(low, high, end)`
per day and never asks whether a position closed. **A multi-day hold is several consecutive days of
non-zero increments instead of one**, each measured against the previous day's mark:

```
day 1 of a hold    18:00 (prev) -> 16:00     the C1 window, entered fresh
day 2..k           16:00 (prev) -> 16:00     held through, including the 17:00-18:00 halt
                   then re-enter at the next 18:00
```

**The one genuine modelling choice, stated rather than buried: notional is fixed at hold entry and
carried to the exit.** A position is not re-sized mid-hold. D440's `run_cell` re-sizes daily
because there every day was its own hold.

## 2. What hold length actually changes, and it is almost nothing

| `k` days | hours | daily sd | mean bp | p99 MAE | breach 1× | **flat share of the day** |
|---:|---:|---:|---:|---:|---:|---:|
| **1** | 22 | 1.042% | 5.21 | 3.376% | 1.694% | **8.3%** |
| 2 | 46 | 1.061% | 5.92 | 3.415% | 1.733% | 4.2% |
| 3 | 70 | 1.054% | 5.49 | 3.621% | 1.772% | 2.8% |
| 5 | 118 | 1.060% | 5.44 | 3.486% | 1.733% | 1.7% |
| 10 | 238 | 1.064% | 5.72 | 3.587% | 1.733% | 0.8% |
| **20** | 478 | **1.065%** | 5.74 | **3.707%** | **1.772%** | **0.4%** |

**The only column that moves materially is the one nobody was arguing about — the share of the day
spent flat, 8.3% → 0.4%.** Everything the rules read is flat in `k`.

> **THE MECHANISM, AND IT IS THE POINT OF THE RECORD.** The shape constraint is an argument about
> **per-hold** σ: a longer window carries more standard deviation, so one contract makes the
> `$150` day, so the contract count stays under the `4%` ceiling. **But the MLL ratchets DAILY and
> the qualifying threshold is DAILY.** Marked daily, a 20-day hold is twenty ordinary days — its
> per-hold σ is `√20` larger and **entirely irrelevant**, because nothing in the rulebook ever sees
> a hold.
>
> **The lever is real at the frequency the strategy is described in and absent at the frequency the
> account is judged at.**

## 3. The curve, and its null

| `k` | 1 | 2 | **3** | 5 | 10 | 20 |
|---|---:|---:|---:|---:|---:|---:|
| `V` | 114 | 75 | **198** | 8 | 97 | 91 |
| funded years | 0.35 | 0.07 | 0.41 | 0.07 | 0.32 | 0.25 |

**The treatment is a max over 6 hold lengths × 4 risk fractions, so the null resamples the day
sequence in circular blocks, rebuilds the whole grid and takes its max** — 60 replicates, block 20:

| | |
|---|---:|
| observed argmax | **198** (at `k` = 3) |
| **null p50** | **662** |
| null p95 | 2,086 |
| **`P(null ≥ observed)`** | **0.883** |

**Inside the null, and again below its median** — the same signature D458 found and the fifth
appearance of the clustering result: **block-resampling improves the account, so every resampling
null on this series is systematically generous.**

**`V` is not monotone in `k`.** **No `k` clears P4** — funded lives 0.07 to 0.41 years against
three.

**`[REP]`: `k` = 1 here gives 114 against D458's `H` = 1320 giving 92.** The two differ only in the
sizing rule — per-hold here, per-day there — and are otherwise the same object, which is the
consistency check this study owed its predecessor.

## 4. Predictions

| | prediction | outcome |
|---|---|---|
| **X1** | daily sd, p99 MAE and breach all rise **monotonically** with `k` | **WRONG, and informatively** — they barely move at all, and breach is not monotone. **This failure IS §2** |
| **X2** | no identifiable optimum in `k` | **CONFIRMED** — `p` = 0.883 |
| **X3** | `T2` fails at every `k`, and **by more** than within the day | **HALF** — fails at every `k`, but by no more: 0.07–0.41 years here against D458's 0.06–1.25 |
| **X4** | "longer is better" still does not hold on its own range | **CONFIRMED** |

**X1 is the useful miss.** I predicted longer holds would be riskier per day and they are not,
because a daily mark does not care how long a position has been open. **Expecting the risk to scale
with hold length was the same category error the shape constraint makes, and I made it in the
prediction while setting out to test it.**

## 5. What this closes, and the one thing it does not

- **The shape constraint has now been tested on its own range and is not supported.** *"The
  scissors close on long windows, not on small edges"* was the prop research's single most
  actionable structural claim and the last standing route to a fifth candidate.
- **It is not refuted as an observation about the SEARCH** — every prop rejection in that review
  really was a size rejection. **What fails is the inference that widening the window fixes it.**
- **Nothing here rescues C1**, which fails P4 elevenfold on the instrument
  ([D452](D452-RESULT-D440-on-the-instrument-same-verdict-and-clustering-explains-94-percent-not-83.md)).
- **What is NOT tested: a hold whose length is CONDITIONAL** rather than fixed. Every `k` here is a
  fixed calendar rule. A rule that exits on a state — the abstention family
  ([D442](D442-RESULT-O1-clears-the-ledgers-own-criterion-and-dies-inside-the-rotation-null-and-the-mask-breaks-the-inactivity-rule.md))
  is its gating cousin and died on its own controls — **is a different object and is untouched
  here.**

## 6. A note on the record, not the result

**`docs/BOOK_PROP.md` is being edited by a concurrent session while this ran**, so this record
does not amend it. **The prop book's C1 and candidate sections now have five records
(D440, D442, D451, D452, D458, D459) that have not been folded into them**, and folding them is a
single careful pass that should happen when that file is not moving.
