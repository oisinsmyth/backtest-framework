# D458 RESULT — the hold-length curve: the path blade is real and monotone, and there is NO identifiable optimum — the observed argmax sits BELOW its own null's median

**MEASUREMENT record. No hurdle is claimed and no candidate is admitted.** The last open item on
the prop track: the hold-length curve named in
[`docs/prop firm leads/01`](../prop%20firm%20leads/01-prop-lead.md) §4 and
[D452](D452-RESULT-D440-on-the-instrument-same-verdict-and-clustering-explains-94-percent-not-83.md)
§7. **Runner:** `scripts/d458_hold_length_curve.py`. **Fixtures built:**
`data/fixtures/es_minute_bars.parquet` (6,844,532 rows), `data/fixtures/es_hold_ladder.csv.gz`
(3,584 holds). **Evidence:** `data/d458_hold_length_curve.json`.

---

## THE ANSWER

> **Both 4% bounds are drawn for the first time. The PATH bound is real, monotone and
> well-measured. The VALUE curve has no identifiable optimum at all — the observed argmax of 507
> sits BELOW its own null's MEDIAN of 917, at `p = 0.760`.**
>
> **And no hold length on the ladder clears P4. Funded lives run 0.06 to 1.25 years against a
> three-year bar.**

## 1. The path blade — real, monotone, and the half nobody could measure before

**Entry is C1's 18:00 ET Globex reopen, unchanged; the hold is closed after `H` minutes of clock
time rather than at 16:00.** 3,584 holds, 2010-06-07 → 2026-09-09.

| `H` | hours | bars | sd/hold | p99 MAE | breach 1× |
|---:|---:|---:|---:|---:|---:|
| 240 | 4 | 241 | 0.321% | 1.388% | 0.056% |
| 480 | 8 | 480 | 0.406% | 1.667% | 0.140% |
| 720 | 12 | 720 | 0.519% | 2.087% | 0.167% |
| 960 | 16 | 960 | 0.679% | 2.595% | 0.474% |
| **1320** | **22** | 1,319 | **1.028%** | **3.388%** | **1.116%** |

**Monotone at every step in all three columns.** **This is D259's and D440's blade, and it is the
first time it has been drawn at anything but C1's fixed 22 hours** — the ES minute series is what
made it measurable.

## 2. The value curve — and why its peak is not a finding

| `H` (min) | 30 | 60 | 240 | 480 | 720 | 840 | **960** | 1080 | 1200 | **1320** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `V` | **335** | 39 | 57 | 9 | 86 | 186 | **507** | 215 | 476 | **92** |

**Adjacent hold lengths swing by ±300. A 30-minute hold and a 16-hour hold both score high with
everything between them lower.** That is not a peak.

### The null, scored the same way the treatment is

**The treatment is an argmax over 13 hold lengths × 4 risk fractions = 52 cells.** So the null
resamples the hold sequence in circular blocks, **rebuilds the whole 52-cell grid, and takes its
max** — 100 replicates, block 20.

| | |
|---|---:|
| **observed argmax** | **507** (at `H` = 960) |
| null max-over-grid, p50 | **917** |
| null p95 | 1,997 |
| null max | 3,336 |
| **`P(null max ≥ observed)`** | **0.760** |

> **The observed optimum is not merely inside the null — it is BELOW THE NULL'S MEDIAN.** A
> block-resampled version of this same data typically produces a *better* best-of-52 than the real
> sequence does.

**And the null's argmax location is scattered**: 1200 (21 times), 960 (21), 1320 (19), 1080 (14),
720 (6), 30 (6). **Where the maximum lands is essentially random, which is what a flat curve plus
noise looks like.**

> **This is [D442's addendum](D442-ADDENDUM-the-two-apparent-wins-were-selection-across-four-risk-fractions.md)
> applied BEFORE publication rather than after.** That record found two apparent wins that cleared
> a null scored at one fixed grid point while the treatment was an argmax over four, with a
> selection premium larger than the effect. **Here the null was built first, and it killed the
> finding before it was written down.**

### And the clustering signature appears a fourth time

**The null's median (917) EXCEEDS the observed (507)**, which means block-resampling the sequence
**improves** the account. That is the same mechanism
[D440](D440-RESULT-the-gaussian-was-worth-five-sixths-of-the-value-and-it-is-clustering-not-kurtosis.md)
measured at 82–86%, [D442](D442-RESULT-O1-clears-the-ledgers-own-criterion-and-dies-inside-the-rotation-null-and-the-mask-breaks-the-inactivity-rule.md)
saw in its bootstrap centre, and [D452](D452-RESULT-D440-on-the-instrument-same-verdict-and-clustering-explains-94-percent-not-83.md)
sharpened to 94% on the instrument: **breaking the serial structure helps, so any resampling null
is systematically generous.**

## 3. What is robust regardless of the null

- **No hold length clears P4.** Funded lives: **0.06 to 1.25 years against 3.00.** Under the
  [R11 ruling](../RULES.md#r11) that is the operative statistic, and the shortfall is an order of
  magnitude at every single `H`.
- **The research's "longer is better" is NOT supported.** *"The scissors close on long windows, not
  on small edges"* predicts `V` rising with `H`. **`V` is not monotone in `H`, and C1's own 22-hour
  window scores 92 against a 30-minute hold's 335.** **But the null forbids the reverse claim too:
  the curve cannot distinguish any `H` from any other.**
- **The path bound is monotone and the value bound is flat.** **The two blades the shape constraint
  described do not close on a point, because only one of them is a curve.**

## 4. Predictions

| | prediction | outcome |
|---|---|---|
| **U1** | `V` is **not** monotone increasing in `H` | **CONFIRMED** |
| **U2** | funded life **falls** monotonically as `H` rises | **WRONG** — not monotone |
| **U3** | the `V` argmax is **interior and well below 1,320** | **TECHNICALLY right, SUBSTANTIVELY VOID** — the argmax is at 960, and §2 shows it is not an optimum. **Scored as failed, because a prediction that a noise peak will be interior is not a prediction about the world** |
| **U4** | `T2` fails at **every** `H` | **CONFIRMED** — 0.06 to 1.25 years |

## 5. An operational episode, recorded because I got it wrong out loud

**Mid-study the raw DBN began vanishing from `temp/databento/` — 8 of 14 files disappeared during
a single build.** I reported this as deletion under `temp/`'s documented "deletable any time"
contract, and **preserved a 1.69M-row fragment** covering 2012–2015 and 2024–2025.

**It was not a deletion. The concurrent acquisition session was MOVING the raw out of deletable
`temp/` into `data/raw/databento/`** — the right call — **and had already updated the `RAW` path
inside D448's and D449's runners.** All 26 files are intact with complete coverage.

**What survives the correction, and is worth keeping:** `data/raw/` is **gitignored**, so 104 GB of
raw is durable on this machine and absent from the repo. **The ES subset is now preserved as
`data/fixtures/es_minute_bars.parquet` — 6.8M rows, 58 MB — which is what makes all five ES studies
reproducible without it.** **Re-reading 625M raw rows three times to recover the same 4.9M was the
actual mistake, and the false alarm is what exposed it.**

## 6. What this closes

**The prop track's open list is now empty.** D258's four candidates resolved; `O1` resolved; C1
measured end-to-end on the instrument and failing P4 elevenfold; the settlement, untraded-window
and entry-print caveats all discharged; **and the hold-length curve — the last route to a fifth
candidate — has no optimum to find.**

> **A fifth candidate still needs a new mechanism. What this record removes is the hope that one
> was hiding in the hold length.**

## 7. What it leaves

1. **`H` > 22 hours is NOT tested**, and the reason is stated in the runner: a multi-day hold
   ratchets the floor at each EOD while the position stays open, which D440's lifecycle cannot
   express without a modelling assumption this study would then be testing rather than using.
   **The research's shape constraint is strictly an argument about longer windows, so the range it
   actually points at remains unmeasured.**
2. **The `q − r` regression** D451 §6 names, still owed.
3. **The thin-print explanation** for why the equity proxy overstates excursion (D451 §6, D449
   amendment 2), still a candidate and still unmeasured.
