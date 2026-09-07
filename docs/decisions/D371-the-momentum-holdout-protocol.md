# D371 — the momentum book's out-of-sample protocol: both gates, one read, built and rehearsed but NOT spent

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8), and before the withheld fixture is
touched by anything that reads a return.
**Date:** 2026-09-07 · **Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**THIS RECORD DOES NOT SPEND THE READ.** It builds the protocol, proves the code path on the mining fixture, and
stops. The read runs once, later, on the principal's explicit go, via a flag that does not fire by accident.

---

## 0. Why now, and why not yet

D369 settled what in-sample work can settle:

- **the trigger is established** — 0 of 10,000 time rotations beat it, at 143–164 standard errors;
- **the nine-condition gate clears everything** — its own rotation at 32.9 SE, a best-of-ten multiplicity control
  at 32.3;
- **the one-condition gate is undecidable here** — 3.2 SE against its own rotation, **−1.0 SE (UNRESOLVED)**
  against multiplicity, with a margin (0.034) the same size as its standard error (0.035). **No draw count fixes
  that**: the effect and the multiplicity penalty are the same magnitude.

The last point is why the read is now worth designing. **An out-of-sample segment is the only instrument that can
separate those two gates**, because it is the only evidence that multiplicity does not price. But designing it and
spending it are different acts, and the principal has directed that only the first happens now.

## 1. The fixture

`data/fixtures/us_shorts_daily_holdout.csv.gz` — **803 names disjoint from the mining set** (asserted from both
fixtures' metadata), the same 2010–2026 span, its own events file, and its EDGAR deal file already pulled
(`us_shorts_daily_holdout_deals.json`). **It has never been read.**

D357 built the re-pointing machinery — score cache, D303 arrays, census and floor, open fill, floored market, the
shared prep under its own key — and asserts the re-pointed pipeline reproduces the mining fixture's committed
numbers to 0.0 before any holdout array is built. **D371 reuses that machinery rather than rebuilding it**, and
inherits its guarantee that `--dry` reads no return.

## 2. Both constructions, one read — and the multiplicity that creates

The principal has directed that **both gates are tested on the same read**:

| | gate | in-sample standing (D369) |
|---|---|---|
| **A** | **S6** — all nine conditions (≡ C9 + C4) | clears its rotation at 32.9 SE, multiplicity at 32.3 |
| **B** | **C9** — the index at a 252-bar high, alone | clears its rotation at 3.2 SE, multiplicity **UNRESOLVED** |

**Two hypotheses on one clean sample is two tests, and the record prices them as two.** Each construction must
clear the **p97.5** of its nulls, not the p95 — a Bonferroni split of α = 0.05 across the two. This is stated
here, before the read, so that the adjustment cannot be chosen afterwards to suit whichever passes. **The
unadjusted p95 figures are reported beside, labelled as such**, so a reader can see both.

Everything else is D366's construction, frozen and identical for both arms: `mom_252_21`, enter above rank 95
with the gate open, **single exit rank 90** (D367: the 80/90 split is worth 0.02 bp/bar and is not a degree of
freedom), **252-bar cap — a declared holding-period constraint, not a tuned parameter**, equal-weight long,
dollar-volume-weighted short of the eligible universe **rebuilt on whatever universe is being traded** (D370's
correction), next open on both legs, hedge borrow at GC 50 bp/yr and measured rebalancing charged, PUB primary
with PB beside.

## 3. The protocol — run twice, as declared in D367 §5

> **The baseline is that segment's OWN gate-rotation median**, computed on the segment being read, never carried
> over from the mining fixture. In sample it is +3.8; the effect to detect is roughly +4 bp/bar, not +8.

Each construction is evaluated **twice**:

1. **HOLDOUT ALONE** — the 803 withheld names, on their own.
2. **COMBINED** — mining and holdout pooled.

**Both are reported. Neither is chosen after the fact.** The holdout-alone result is the evidence; the combined
result is context and is labelled as such, because it is contaminated by the mining fixture the construction was
selected on.

**Nulls, computed separately on each segment:** GATE-ROT (the gate circularly shifted, on-share and circular
run-length multiset preserved) and A′ (per-name time rotation within eligible bars), **2,000 draws each** — the
p95 SE at 2,000 was 0.05 or better in D369, ample for the margins in question, and the achieved SE is reported.
ROT (24 rank shifts) is exhaustive and carries no sampling error.

## 4. Hurdles — all six, per construction

| | hurdle |
|---|---|
| **H1** | PUB net bp/bar **> 0** after hedge borrow and rebalancing |
| **H2** | net above the **p97.5 of BOTH nulls** on the holdout segment (GATE-ROT and A′), each stated with its bootstrap SE, and **UNRESOLVED if the margin is under 2 SE** |
| **H3** | the symmetric 1% trimmed mean per trade exceeds the per-trade round trip |
| **H4** | **no single trade above 10% of the ledger's P&L** |
| **H5** | at least **10 names** to half the P&L |
| **H6** | PUB net Sharpe **> 0** |

**H4 is retained even though the in-sample book fails it.** D366's S6 book has GME at **11.7%** of all P&L. The
hurdle is kept because a book whose single best trade is an eighth of its P&L is not one this programme should
admit, and because **dropping a hurdle the candidate is known to fail is tuning the hurdle to the candidate.** If
the holdout book fails H4 too, that is the hurdle doing its job, not a surprise.

**Any failure retires that construction.** All six, on the holdout-alone arm, at the adjusted level → the
construction becomes eligible for `BOOK.md` carrying its falsification conditions. **Clearing the hurdles is not
admission** — R8 and the pipeline still apply.

## 5. What this record does now

- **`--pipe`** — re-point the pipeline, assert it reproduces the mining fixture's committed numbers to 0.0.
- **`--dry`** — counts only on the holdout: names, bars, filings applied, floor share, gate coverage. **Reads no
  return.** A static check asserts no path in the dry or prep stages turns `r1T` or `ocT` into a statistic.
- **`--rehearse`** — **the read's exact code path on the MINING fixture**, tiny draw counts, output to `temp/`.
  Not a result. It proves both arms, both segments, the null machinery, the hurdle table and the JSON all execute
  before the one execution that matters.
- **`--read --spend-the-holdout`** — wired, guarded, and **NOT RUN**. It refuses without both flags and without a
  committed construction file naming the two arms.

## 6. Predictions

**Deliberately none for the read itself.** Predictions belong with the read, and the read has not happened; a
prediction written now and reported after would be indistinguishable from one written after. The hurdles in §4
*are* the pre-registered criteria and they are sufficient. This record's own checks are §7's assertions.

When the read is authorised, an addendum will state — **before** the run — the expected direction on each hurdle,
so the read is scored against something and not merely described.

---

## ADDENDUM, 2026-09-07 — the read is authorised; predictions committed BEFORE it runs

**The principal has authorised the first holdout read.** §6 committed that an addendum would state the expected
direction on each hurdle *before* the run, so the read is scored rather than merely described. That is this
section, and it is committed before the fixture is touched by anything that reads a return.

**The construction is frozen in `data/d371_construction.json`**, committed in the same commit as this addendum.
**H4 is unchanged.** I flagged before the read that it will probably fail and that this is the moment to change it
if it is the wrong hurdle; it is retained exactly as written, because relaxing a criterion after seeing that the
candidate fails it — and before the test that would confirm it — is the clearest possible case of tuning the
hurdle to the candidate.

### P1–P8, for the HOLDOUT-ALONE arm

| | prediction | reasoning |
|---|---|---|
| **P1** | **S6's net is > 0.** | The trigger cleared its time rotation at 164 SE with 0 of 10,000 draws beating it. Cross-sectional momentum is the most replicated anomaly there is. |
| **P2** | *(load-bearing)* **S6 clears BOTH nulls at p97.5.** | A′ should be comfortable. GATE-ROT is the genuine uncertainty: the gate is the searched part of the construction, and this is the first evidence multiplicity does not price. |
| **P3** | **S6's net is BELOW the in-sample +8.106.** | Roughly a hundred constructions were searched on the mining fixture. The survivor is likelier to be noise, so shrinkage is expected. A holdout number *above* in-sample would be a surprise worth investigating rather than celebrating. |
| **P4** | **H4 FAILS — the top trade exceeds 10% of P&L.** | Stated publicly before the read. A right-tail book on 803 names concentrates wherever it is pointed; in sample the figure is 11.7% and a smaller universe should concentrate harder, not less. |
| **P5** | **Neither arm passes all six hurdles**, and the binding failure is H4. | P4 plus the expectation that H1, H3, H5, H6 pass. |
| **P6** | **C9's GATE-ROT margin, in SE, is smaller than S6's.** | C9 is the weaker gate in sample (3.2 SE vs 32.9) and undecidable against multiplicity. |
| **P7** | **Era 2's net exceeds era 1's**, as it does in sample (+12.10 vs +0.46). | The weak-premium era-1 regime is a property of the period, not of the mining names, so it should reappear on a disjoint universe over the same span. |
| **P8** | **S6's gate is open on 5–15% of holdout bars.** | The gate is a market condition — an index at a 252-bar high — computed from the holdout universe's *own* floored market. That index is a different series from the mining one, so the on-share will differ from 9.2%, but not wildly. |

### P9–P12 — THE PRINCIPAL'S OWN PREDICTIONS, in their words, entered before the read

The principal asked to put their prediction into the record. Stated: *"I think we will see ann return drop to 16%
and drawdown increase slightly. Not much of a prediction I know but I think it will generalise but lower its
performance. On the combined holdout + mined data I think it will perform better than on the mined data."*

| | prediction | scored as |
|---|---|---|
| **P9** | **annualised net falls to ≈16%** from the in-sample +20.4% | the point estimate is recorded; P9 counts as held if holdout annualised net is in **[12%, 20%]** |
| **P10** | **max drawdown increases slightly** | holdout maxDD **> 3,158 bp** and **< 2×** it |
| **P11** | **it generalises, at lower performance** | holdout net **> 0** and **< +8.106** bp/bar |
| **P12** | **the COMBINED book beats the MINING-only book** | combined 50/50 Sharpe **> 0.887**, the mining-only figure; combined net reported beside |

**P12 is the sharpest of the four and it is not implied by the others.** If the holdout's mean is lower (P11),
the combined *mean* must sit between the two books — so P12 can only hold on a **risk-adjusted** basis, through
the two disjoint universes being imperfectly correlated. It is a prediction about diversification, and it is the
reason the combined arm is computed as a date-aligned 50/50 portfolio rather than as a concatenation.

**A note on where P9–P12 sit against P1–P8.** They are compatible: P3 and P11 say the same thing, and P9 is a
sharper version of it. P12 is the only one making a claim nothing in P1–P8 addresses.

### How the result will be reported

**The holdout-alone arm is the evidence. The combined arm is context and is labelled as contaminated**, because
its mining half is the fixture the construction was selected on.

**One declared deviation from D367 §5's wording.** "Combined data" cannot mean one merged universe: ranking across
the union of 2,376 names is a *different strategy* from the one being read, with a different top 5% on every bar.
What is combined is the **P&L** — the same construction run on each universe, each ranked within itself, the two
per-bar series pooled. That is what holding both books would have earned. The mining series is computed and
stored **before** the read (`--mining-series`, already run) so that nothing about the combined arm depends on
anything learned from the holdout.

**Whatever the six hurdles return, the read is spent and is not repeated.** A failure retires the construction; it
does not license a search for a better one followed by a second read. R8's one-read discipline is the whole point
of the asset.

## 7. Assertions

| | |
|---|---|
| **[DISJOINT]** | the holdout's symbol set is disjoint from the mining set, asserted from both fixtures' metadata |
| **[NOREAD]** | `--dry` and `--pipe` touch no return: a static scan asserts neither stage reaches `r1T`/`ocT` in a reducing call, and the file-open audit reports every holdout path opened |
| **[PIPE]** | the re-pointed pipeline reproduces the mining fixture's committed D366/D369 numbers to **0.0** before any holdout array is built |
| **[REHEARSE]** | the read's code path runs end to end on the mining fixture and produces a complete hurdle table |
| **[GUARD]** | `--read` without `--spend-the-holdout` refuses; `--read` without the committed construction file refuses; both are exercised in the self-test |
| **[FAST]** | the D369 kernel is bit-identical to D366's functions on both constructions |
| **[SHARE]** · **[SE]** | rotations preserve on-share and the circular run-length multiset; every p95 carries a bootstrap SE |
| **[6]** | [DISJOINT], [PIPE], [GUARD] and [SHARE] each raise on a deliberately broken input |

## 8. Files

`docs/decisions/D371-the-momentum-holdout-protocol.md` (this record) ·
`scripts/run_d371_momentum_holdout.py` (stages `--selftest`, `--pipe`, `--dry`, `--rehearse`,
`--read --spend-the-holdout`) · `data/d371_construction.json` (the frozen two-arm construction) ·
`temp/d371_rehearsal_mining.json` (not a result). Reuses `scripts/run_d357_holdout_read.py` for the re-pointing
machinery, `scripts/d369_fast_kernel.py`, `scripts/run_d366_gated_buffer.py`,
`scripts/run_d367_gate_deconstruction.py`, `scripts/d348_prep.py`.

**The holdout fixture is not read by this record.**
