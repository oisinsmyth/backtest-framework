# D373 RESULT — the winners' dip is the retired momentum book at ρ = 0.935, and its only pass over the load-bearing control is one GME trade

**Date:** 2026-09-07
**Pre-registration:** [D373](D373-the-winners-dip-long-and-the-median-criterion.md), committed `aa7bc2f`, amended `462f894` — **both before the runner existed** (R8).
**Runner:** [`scripts/run_d373_winners_dip_long.py`](../../scripts/run_d373_winners_dip_long.py), committed `9d64de7`.
**Artifacts:** `data/d373_winners_dip_long.json`, `data/d373_stage0.json`, `data/d373_ctrl_p{0..4}.json`, `data/d373_segmentation.json`, `data/d373_posthoc.json`.
**Fixture:** the mining prefix only. **No holdout was read.** `data/fixtures/us_shorts_daily_holdout.csv.gz` remains spent-and-closed; `us_shorts_daily_holdout2.csv.gz` (built this session, `59f021e`) remains unspent.

---

## 0. The verdict, first

**Five of the seven pre-registered hurdles fail.** The one that passes against the control that
matters passes by **+4.95 bp per trade**, and **removing a single trade — GME entered
2021-01-04 — takes it below that control's p95.** The pre-registered abandon condition of §9 is met
on its own terms: H7 came back at **0.935**.

| | hurdle | verdict | the number |
|---|---|---|---|
| **H1** | signal: gross mean per trade above every control's p95 | **PASS** | +160.55 vs A′ +105.76, B +51.92, **B_c +155.60**, C +52.72 |
| **H2** | the chain `mean > median > 0`, median above the controls' p95 | **FAIL** | median **+51.55**, below A′'s p95 **+81.42** (−23.2 SE) and B_c's **+87.43** (−52.7 SE) |
| **H3** | era 1 standalone, above A′ and B_c recomputed within era 1 | **FAIL** | era 1 **+16.86** vs A′ p95 +64.60, B_c p95 +77.24 |
| **H4** | breadth | **FAIL** | **18 of 796 names = 2.26%** to reach half the P&L; bar was 10% |
| **H5** | capturability (gate 1e) | **PASS** | open-entry t **5.11**, retention **98.7%** |
| **H6** | cost — reported, gates nothing (R15) | *reported* | net PUB hedged **−0.06 bp/bar**; breakeven **37.10 bp/side** against a measured **37.72** |
| **H7** | independence — reported, gates nothing (R15) | **FAIL** | **ρ = 0.9346** to the retired D365 momentum book over 3,185 shared bars |

**I have not closed this avenue.** R15 reserves that to the principal. What follows is what the
evidence says; the decision is not mine to take.

---

## 1. What was run

The frozen construction of §1: a fresh `rev_5` dip inside the `mom_252_21` **top** decile, entered
**long** at the next open (D340), hedged against the floored equal-weight market, exited at a 40-bar
cap. Primary cell **10:90 / cap 40**, chosen only because it is the cell D359 §6 published; §7 of the
pre-registration prices that choice as a best-of-5.

**3,932 trades, 4,005 entries, 796 distinct names, 3,185 deployed bars, exposure 99.97%,
mean hold 39.94 bars.** The runner reproduces all five of D359 §6's published cells to the decimal
place D359 printed before any null runs (`[MIR]`), so what was nulled is the book that was reported.

**Controls: 2,000 draws** for A′, B_c and C and **1,000** for B, as amended in §4 before the runner
was built — five parts × 400 draws, each part a distinct draw index under a **shared per-name
offset**, so the best-of-5 floor is a max over cells *within* a draw and not across independent draws.
All 2,000 of C's draws were distinct. Parts ran at 5.73–5.90 s/draw.

---

## 2. H1 passes, and the margin is one trade wide

| control | what it holds fixed | p50 | p95 | observed margin |
|---|---|---:|---:|---:|
| **A′** per-name time rotation | the name, not the date | +59.42 | +105.76 | **+54.79** (+41.7 SE) |
| **B** same-day same-RSI-bucket swap | the day and the RSI bucket | +29.80 | +51.92 | **+108.63** (+115.6 SE) |
| **B_c** same-day same-**cohort** swap | the day *and membership of the top momentum decile* | **+126.54** | **+155.60** | **+4.95** (+4.6 SE) |
| **C** random direction on the ledger | the ledger, randomising the sign | +0.62 | +52.72 | above; max +98.06 |

**B_c is the only control that asks the study's actual question.** A′ and B both leave the arm free
to be paid for *being in the top momentum decile at all*, and B_c's centre says exactly what that is
worth: **+126.54 bp per trade of the observed +160.55 is available to a random name drawn from the
same cohort on the same day.** The dip timing is the remaining **+34 bp**, and the control's own p95
sits at +155.60.

**So I looked at the top trade, as the concentration report obliges.**

> **GME, entered 2021-01-04 at $17.25, held the full 40 bars, +40,029 bp — 6.34% of the entire
> ledger's P&L**, at the 83rd percentile of dollar volume on its entry bar.

That single trade is worth **+10.2 bp of the observed per-trade mean**, against a margin of +4.95.
Removing it:

| | mean | vs B_c p95 (+155.60) | vs A′ p95 (+105.76) |
|---|---:|---:|---|
| observed | **+160.55** | **+4.95 ABOVE** | +54.79 above |
| drop top 1 trade (GME 2021-01-04) | **+150.41** | **−5.20 BELOW** | +44.65 above |
| drop top 3 | +143.52 | −12.08 BELOW | +37.76 above |
| drop all 10 GME trades | +151.72 | −3.88 BELOW | +45.96 above |
| drop all 156 entries 2020-11 → 2021-03 | +144.28 | −11.32 BELOW | +38.52 above |
| drop top 20 | +103.91 | −51.70 BELOW | **−1.85 BELOW** |

*(Post-hoc, not pre-registered — [`scripts/d373_posthoc_probes.py`](../../scripts/d373_posthoc_probes.py) probe 1,
persisting `data/d373_posthoc.json`. It re-derives the ledger through the runner's own `pnl_bp` and **asserts it
reproduces the committed report before cutting anything**, and it re-tests against the **stored** control percentiles
rather than re-drawing nulls, so the comparison is to the same distribution H1 used.)*

**H1 passed as pre-registered and I am not retracting the verdict** — the hurdle was written before
the result and the arithmetic is what it is. But the honest reading is that the increment over the
cohort is not robust to its single largest observation, and a hurdle that a January-2021 squeeze can
carry on its own is not evidence that the dip timing works.

---

## 3. H2 — the principal's own criterion, and it fails

The chain the principal tightened this record to on 2026-09-07 is `mean > median > 0`, with the
median also above the controls' p95. **Two of its three legs hold and the third does not.**

- median **+51.55 > 0** — holds
- mean **+160.55** strictly exceeds the median — holds
- **median above the controls' p95 — fails**, and not narrowly: A′'s p95 is **+81.42** (−23.2 SE),
  B_c's is **+87.43** (−52.7 SE). Against B it is **UNRESOLVED** at +1.7 SE.

**The controls have a higher median than the strategy does.** A random name from the same cohort on
the same day produces a *better typical trade*; the arm is ahead only on the mean, and §2 shows what
the mean is standing on. This is the clean statement of the result and it is the one the principal's
own hurdle was designed to extract.

### 3a. The criterion is confounded with holding period — a correction I owe

Earlier in this session I told the principal that `mean > median > 0` **would have flagged the
retired momentum book in sample, before its holdout read was authorised**, on the strength of D365's
mean +334.85 against median −141.37. **I tested that claim and it inverted.**

Re-cutting **D365's own stored per-bar hedged paths** — the identical exposure, nothing changed but
where the trade boundaries fall ([`scripts/d373_segmentation_probe.py`](../../scripts/d373_segmentation_probe.py),
committed `7aa95aa`, which asserts the paths reproduce D365's published figures before re-cutting):

| cut | n | mean | median | chain |
|---:|---:|---:|---:|---|
| 20 bars | 9,365 | +61.11 | +22.68 | **PASS** |
| **40 bars** | 5,147 | **+111.18** | **+10.73** | **PASS** |
| 60 bars | 3,758 | +152.28 | +3.57 | PASS |
| 100 bars | 2,686 | +213.05 | −43.41 | FAIL |
| as stored (~99) | 1,709 | +334.85 | −141.37 | FAIL |

**D365 fails the chain only because it holds ~99 bars. At D373's 40-bar hold it passes.** Compared at
equal segmentation the two books *agree* — both pass at 40, both fail at 100. The mechanism is
arithmetic and not a quirk of these books: summing fat-tailed returns over a longer window lifts the
mean and drops the median, so any long-hold construction eventually fails the chain and any
short-hold one eventually passes, edge or no edge. Per-bar-held normalisation does not rescue it; it
flips at cut 40 in the other direction.

**Scope, because this does not void the study.** D373's H1/H2/H3 hold segmentation **fixed on both
sides** — every null draw is scored through the same exit at the same cap — so the within-study null
comparisons above remain fair, and H2's failure stands. What is not usable is **cross-construction**
comparison of a per-trade median between books that hold for different lengths, which is what I had
proposed to do. This is `CLAUDE.md` §10 biting exactly where it says it will.

---

## 4. H3 — era 1 is inside its own controls

Era 1 (entry bar in the first half of the span): **1,248 trades, +16.86 bp per trade**, against A′'s
p95 of **+64.60** and B_c's of **+77.24**. Positive, and comfortably inside both.

**Q3 was the AGAINST prediction and it HELD.** §2 of the pre-registration recorded this candidate at
13.5× era 2 over era 1, and the retired book paid +0.46 in era 1 against +12.10 in era 2 before
failing out of sample. The same shape is here. Whatever the arm is measuring, it is not something
that was present in the first half of the sample.

---

## 5. H4 — breadth fails on one leg of three

| leg | value | bar | |
|---|---:|---:|---|
| names to half the P&L, as a share of names traded | **18 / 796 = 2.26%** | ≥ 10% | **FAIL** |
| top-1 **name** share of P&L | 5.74% | ≤ 15% | pass |
| top-5 name share | 20.62% | ≤ 50% | pass |

The concentration bar is the one that fails, and it fails by 4×. Note the two passing legs are
**name** shares; the top single **trade** is 6.34%, also inside the 15% bar. Q7's scorer reads the
name share, so its "held" is correct on either reading, but the record should say which quantity it
checked.

**A standing doubt, unresolved and flagged again.** Nothing in this programme has ever cleared the
10% names-to-half bar. That is either a real and consistent property of every construction tried
here, or the bar is mis-calibrated. D373 cannot distinguish those, and I am not going to argue for
whichever reading suits the candidate.

### AMENDMENT, 2026-09-07 — **H4 is corrected from FAIL to PASS. It was the bar.**

The doubt above was settled the same day by
**[D374](D374-RESULT-the-breadth-bar-was-unreachable-and-it-failed-the-most.md)**,
which computed the concentration family **per null draw** on this exact ledger.

- Across **4,952 defined draws in three arms**, the most diversified random book reached **2.98%**.
  The median reached **0.63%**. **Nothing came within a factor of three of the 10% bar.**
- This book's **2.2613% sits at the 100.00th percentile of its own nulls** — above A′'s *maximum*,
  with **0 of 1,971** A′ draws and **0 of 981** B draws as diversified.
- **The 10% threshold was unreachable by construction**, and D373 §5 states where it came from:
  "calibrated to exclude the shape that just failed".

**H4 → PASS** under the replacement hurdle H4′ (`names_to_half_share ≥ the study's own A′ p05`,
here 0.2488%). The **top-1 and top-5 bars are dropped entirely** — D374 §4 shows the statistic is
unbounded above and explodes in ~12% of draws, so the 5.74% and 20.62% "passes" recorded above were
near-worthless too.

**D373's overall verdict is unchanged.** H2, H3 and H7 still fail, H7 at ρ = 0.935, and §9's abandon
condition is still met. What changes is that **one of the five failures was the hurdle's fault, not
the book's** — by its own null this was the best-diversified book available. The table in §0 and the
figures in this section are left exactly as first committed; this amendment supersedes the H4 row.

---

## 6. The four groups, in full

**Performance, net and gross side by side** (path-variant, bp/bar, the deployed 50-slot book):

| | gross | net PUB | net PB | vol | Sharpe gross | Sharpe net PUB | maxDD |
|---|---:|---:|---:|---:|---:|---:|---:|
| hedged | +3.859 | **−0.063** | +2.265 | 95.60 | 0.641 | **−0.010** | 2,989 bp |
| unhedged | +8.626 | +4.704 | +7.031 | 168.25 | 0.814 | — | 5,571 bp |

Exposure **99.97%**, flat on 1 bar of 3,186. Turnover **2.52%** of the book per bar, 49.8 positions
held, 317 entries/year, mean holding run 39.9 bars, dead-name share 16.4% of trades (gate 1g).

**Measured, not assumed** (per `CLAUDE.md`): Corwin–Schultz half-spread of the names actually held is
**37.72 bp**; median held price **$44.66**; median held dollar volume **$49.9m**. The 4-crossing
breakeven is **37.10 bp/side**. **The book misses breakeven by 0.62 bp/side** — it is not
approximately at breakeven, it is just the wrong side of it, on PUB's own convention. On PB's
14.67 bp it clears comfortably (+2.26 bp/bar, Sharpe 0.376). Cost gates nothing here (R15); this is
reported so the reader knows the signal question was answered without it.

**Trade distribution** (path-invariant, per trade — never compared to the bar figures above):

count 3,932 · mean **+160.55** · median **+51.55** · win rate **51.6%** · payoff 1.195 ·
hold mean 39.94 / median 40.0 · skew **+2.72** · excess kurtosis **+46.6**

Trimming 1% from both tails (k = 39), all three means as the rule requires:

| ex-top | ex-bottom | symmetric trim |
|---:|---:|---:|
| **+73.24** | +219.31 | **+131.70** |

The mean sits **above** its median, so the **right** tail is doing the work — the opposite of D285's
tell. The symmetric trim survives at +131.70, which is the reassuring number; the ex-top figure of
+73.24 is the one that matters against a B_c centre of +126.54.

**What the winners depend on:** 18 names to half the P&L; top-1 name 5.74%, top-5 20.62%, top-10
34.04%; **12 of 14 years profitable (85.7%)**; dead 643 trades @ +95.95 vs alive 3,289 @ +173.18;
below-median price ($49) 1,966 @ **+183.53** vs above 1,966 @ +137.57 — the edge is larger in the
cheaper half, which is where cost in bp is worst.

**Nulls, distribution not percentile** — the full p50/p95 table is §2. The decisive fact is that
**B_c's p50 is +126.54 against a cohort base rate of 3.85 bp/bar**: the control is not centred near
zero, and any reading of this study that quotes the observed +160.55 without it is meaningless.

---

## 7. H5 and H7

**H5 PASS.** Open-entry mean **+160.55** vs the close-signal version's **+162.74** — retention
**98.66%**, gap 2.19 bp, open-entry t **5.11** against bars of 2.0 and 50%. The signal is not an
artefact of using the signal bar's own close. *(The close-fill panel had to be built for this run;
it asserts the two fills actually differ before comparing them, so the 98.7% is not two identical
books agreeing with themselves.)*

**H7 FAIL, and this is the finding.** Correlation of the deployed bar series to the **retired** D365
momentum book, net PUB, over **3,185 shared bars: ρ = 0.9346**, against a stated bar of 0.50.

It is not the market showing through — each book's own correlation to the floored market is small
(**0.145** for D373, **0.080** for D365) and the **partial correlation controlling for the market is
0.936**, essentially unchanged from the raw figure. It is shared positions:

- **70.1%** of D373's held name-bars are also held by D365
- Jaccard **0.507**
- **683 of 796** distinct names shared (D365 traded 709; 110,060 of D373's 157,053 held name-bars are D365's too)

*(Both readings from [`scripts/d373_posthoc_probes.py`](../../scripts/d373_posthoc_probes.py) probe 2, which asserts its
raw correlation equals the runner's before decomposing it.)*

**D373 is the retired momentum book re-expressed with a shorter hold.** D371 spent the programme's
first holdout read on that book and retired it out of sample.

Against D371's own S6 and C9 holdout series **no correlation was computed, deliberately**: those are
2,734 and 2,752 bars on **803 unseen names**, a different universe, and a cross-fixture correlation
would not answer the question H7 asks. That is recorded as not-comparable rather than as a number.

**Q4 is FALSIFIED.** I predicted |ρ| of 0.2–0.5. It is 0.935.

---

## 8. Predictions, scored

| | prediction | outcome |
|---|---|---|
| **Q1** | the mean clears B_c's p95 — the dip carries timing inside the winner pool | **HELD** — by +4.95 bp, and §2 shows one trade carries it |
| **Q2** | the chain holds, median above all controls' p95 | **FALSIFIED** |
| **Q3** | *against:* H3 fails — era 1 ≤ 0 or inside its controls | **HELD** |
| **Q4** | \|ρ\| to the retired books is 0.2–0.5 | **FALSIFIED** — 0.935 |
| **Q5** | capturability retention ≥ 50% | **HELD** — 98.7% |
| **Q6** | the horizon peak on gross per trade is at the **grid edge** (cap 60), not interior | **HELD** — cap 5/10/20/40/60 = +39.11 / +68.62 / +122.36 / **+160.55** / **+235.73**; the peak is at the edge and is therefore **unresolved, not concluded** (gate 1i). The median is non-monotone: cap 20 (+52.50) is above cap 40 (+51.55) |
| **Q7** | the top trade is ≤ 15% of the ledger | **HELD** — top name 5.74%, top trade 6.34% |

Six of seven scored; **two of the four forward predictions were falsified**, and the one that was
made against the candidate held.

---

## 9. The abandon condition, stated and not exercised

§9 of the pre-registration reads: *"**H7 > 0.5** → it is the momentum book re-expressed, and the
momentum book has been read out of sample and retired. Nothing further is owed."*

**H7 = 0.935. The condition is met.** Under R15 the avenue is the principal's to close, so this
record states the condition is met and stops there.

### AMENDMENT, 2026-09-08 — **THE AVENUE IS RETIRED BY THE PRINCIPAL**

**RETIRED 2026-09-08.** The winners'-dip long, and the wider avenue of *timing an entry inside the
`mom_252_21` top decile*, are closed. Recorded here in writing rather than by quiet edit; nothing
above this line has moved.

**The evidence the decision rests on is broader than this record's own.** By the time it was taken,
**three unrelated methods had measured the same thing** — see
[FINDINGS §52](../FINDINGS.md):

| | lens | measurement |
|---|---|---|
| **this record** | return per trade | `B_c` centres at **+126.54** of the observed **+160.55** |
| **[D376](D376-RESULT-two-unrelated-books-here-correlate-at-0.48-and-two.md)** | covariance | two books sharing only cohort membership correlate at **+0.923** |
| **[D377](D377-RESULT-the-beta-hedge-is-adopted-and-it-fixes-seven-percent-of.md)** | hedge | removing the cohort takes the gross mean to **+34.08** and the median to **−30.74** |

**Roughly 80% of the edge was exposure to the momentum decile.** And D376 showed the excess over the
cohort baseline was **+0.011**, not the +0.43 that H7's 0.935 against a 0.50 bar implied — D373 was
not unusually similar to D365; it was **as similar as any two cohort books are**.

**What the retirement does NOT do.** It does not withdraw a measurement. H1 cleared its four controls
as pre-registered and that stands; so do H5, the nulls, and the segmentation diagnostic of §3a. The
H4 correction of D374 stands too — **that failure was the bar's fault, and by its own null this was
the best-diversified book available.** The avenue closes on the **size and provenance** of the
increment, not on a failed null.

**Nothing was in either book, so no book is amended.** `docs/BOOK.md` remains S1 and S2; the prop
book remains empty.

### SECOND AMENDMENT, 2026-09-08 — **THE AVENUE IS REOPENED, NARROWLY**

**REOPENED 2026-09-08 by the principal (R15), on one specific question that the retirement did not
answer and could not have.**

The retirement above rests on **level** evidence — D373's `B_c` centre and D377's hedge — and those
stand unchanged. What it did **not** rest on is any measurement of **entry timing inside the
cohort**, because no control in the programme tests it:

- **A′** rotates to any eligible bar, most of them outside the top decile, so it conflates timing
  with cohort membership.
- **B_c** holds the day fixed by construction and is silent on day choice.

The reopening also corrects a claim in this record's own lineage: **ρ = 0.923 between cohort books
bounds their co-movement, not their means.** Two books can correlate that highly and earn very
differently, so the covariance evidence never spoke to whether a better-timed entry earns more. That
is recorded at [FINDINGS §52's correction](../FINDINGS.md) and set out as a gap at §52a.

**The reopening is narrow and it is not a reprieve.** It authorises exactly one pre-registered test —
**[D378](D378-does-the-entry-day-matter-inside-the-cohort.md)**, the cohort-conditioned time rotation
`A′_c` — on the already-spent mining prefix. It does not restore the construction, does not touch
either book, and does not authorise a holdout read. **If D378 fails, the retirement above stands as
written and this amendment expires with it.**

For whatever the decision is, the ledger of what this study cost: **one best-of-5 search** on the
already-spent mining prefix, priced in §7 and taken under the principal's ruling of 2026-09-07 that a
brand-new construction may mine spent in-sample data so long as nothing crosses into a holdout.
**Nothing crossed.** No holdout was read, and holdout #2 was built during this study without being
scored.

## 10. What this study did not measure

- **Opportunity cost of the slot.** `sel = rank < N_SLOTS`, so the refill pool is the slot count and
  an exit on a still-selected name re-enters it. Unmeasured here as everywhere else (FINDINGS §10).
- **Whether the +34 bp over the cohort survives outside 2021.** §2's window cut is one crude probe,
  not a study; it removes 156 trades and takes the mean below B_c's p95, which is suggestive and
  nothing more.
- **Whether H4's 10% bar is right.** Flagged in §5, still open.
- **Anything out of sample.** Neither fixture was read.

---

*Result committed separately from the pre-registration, per R8. Nothing is admitted to
[`docs/BOOK.md`](../BOOK.md) or [`docs/BOOK_PROP.md`](../BOOK_PROP.md); the prop book remains empty.*
