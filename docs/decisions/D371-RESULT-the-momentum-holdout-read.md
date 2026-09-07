# D371 RESULT — the read is spent and the construction failed: both gates RETIRED

**Status:** RESULT. Pre-registration `0e771e8` (with the addendum carrying all twelve predictions), construction
frozen in `data/d371_construction.json`, runner and prerequisites committed before the read.
**Date:** 2026-09-07 · **Area:** Strategy research · **personal track**

> ## HOLDOUT READS SPENT: **1**. Programme total: **1**.
> The read ran once, on 803 names disjoint from the mining set, on the principal's explicit authorisation.
> **It is not repeated.** Per §4 of the pre-registration, any failure retires the construction.

**Predictions: 5 of 8 mine, 2 of 4 the principal's. The load-bearing one — P2 — is FALSIFIED.**

---

## Headline

**Both constructions failed four of six pre-registered hurdles and are retired.** The book does not survive on
data it has never seen: net falls from **+8.11 to +3.19** bp/bar, Sharpe from **0.887 to 0.344**, and — the part
that ends it — **outside its top five names the book loses money.**

| arm | open% | gross | net | Sharpe | ann | maxDD | trades | hurdles | |
|---|---|---|---|---|---|---|---|---|---|
| **S6** (nine conditions) | 9.4% | +4.94 | **+3.19** | 0.344 | +8.0% | 6,234 bp | 561 | H1 ✓ H2 ✗ H3 ✗ H4 ✗ H5 ✗ H6 ✓ | **FAIL** |
| **C9** (252-bar high alone) | 9.6% | +4.87 | **+3.13** | 0.339 | +7.9% | 6,336 bp | 570 | H1 ✓ H2 ✗ H3 ✗ H4 ✗ H5 ✗ H6 ✓ | **FAIL** |

## 1. The nulls — and the correction I owe the record

2,000 draws per arm per null, every p95 with its bootstrap SE, tested at the **p97.5** Bonferroni bar fixed
before the read because two constructions share one sample.

| arm | null | p50 | p95 | **p97.5** | SE | observed | margin | in SE | beat | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| S6 | GATE-ROT | +0.138 | +3.388 | +3.927 | 0.069 | +3.187 | −0.740 | **−10.7** | 122 | **FAILS** |
| S6 | A′ | −0.534 | **+2.804** | +3.513 | 0.131 | +3.187 | −0.326 | **−2.5** | 76 | **FAILS** |
| C9 | GATE-ROT | +0.142 | +3.128 | +3.715 | 0.084 | +3.132 | −0.583 | −6.9 | 100 | **FAILS** |
| C9 | A′ | −0.603 | +2.870 | +3.667 | 0.136 | +3.132 | −0.535 | −3.9 | 83 | **FAILS** |

**I predicted, twice and in writing, that A′ would clear and GATE-ROT would be the binding failure — that the
trigger survived out of sample and only the gate died. That was wrong. Both fail.**

The precise reading, which matters for what comes next:

- **A′**: S6 clears the *conventional* p95 (+3.187 against +2.804) and fails only the pre-registered p97.5
  (+3.513). It sits at the **96.2nd percentile** — above 95, below 97.5. **The multiplicity adjustment is what
  converts it from a marginal pass into a fail**, which is the adjustment doing exactly the job it was fixed in
  advance to do.
- **GATE-ROT**: fails below even the unadjusted p95. **93.9th percentile.**

Against in-sample — A′ at **0 of 10,000** draws (164 SE) and GATE-ROT at **62 of 10,000** (32.9 SE) — both
collapsed. The trigger is *borderline*, not intact.

## 2. What ends it: outside the top five names, the book loses money

| | S6 | C9 |
|---|---|---|
| trades | 561 | 570 |
| mean / median per trade | +115 / **−37** | +109 / **−59** |
| win rate | 49.0% | 48.6% |
| **1% trimmed mean vs round trip** | **+63.9 vs 94.8** | +59.1 vs 94.2 |
| names to half the P&L | **2 of 255** | **2 of 259** |
| **top 1 / 5 / 10 name share** | **36% / 142% / 231%** | **40% / 151% / 242%** |
| top trade | **CAR, 2021-04-19, $78.15, held 252 bars (the cap), +19,325 bp = 30.0% of all P&L** | same trade, 31.1% |

**The top-name shares exceeding 100% are the finding.** The top five contribute 142% of total P&L, so everything
outside them is **net negative**; outside the top ten the remainder loses 131% of what the book makes. Two names
of 255 reach half the P&L, against twelve of 515 in sample.

**H3 says the same thing in cost terms:** trim 1% from both tails and the average trade returns **+63.9 bp
against a 94.8 bp round trip** — it does not cover its own costs. The book is profitable only through a handful
of extreme winners, and on this universe that handful is two names and one Avis Budget squeeze.

**One genuine surprise, in the construction's favour:** era 1 was fine — **+2.98 against era 2's +3.31**. The
in-sample era-1 weakness (+0.46 vs +12.10) that no gate could fix simply did not reappear.

## 3. The combined arm — context, not evidence

Declared before the read as contaminated, because its mining half is the fixture the construction was selected on.
Computed as the **date-aligned 50/50 portfolio**, not a concatenation (both fixtures span the same calendar).

| | shared bars | net | Sharpe | ann |
|---|---|---|---|---|
| **combined 50/50** | 2,724 | +5.781 | **+0.716** | +14.6% |
| mining alone, same bars | 2,724 | +8.366 | 0.911 | — |
| holdout alone, same bars | 2,724 | +3.195 | 0.347 | — |
| **correlation between the two books** | | | **+0.545** | |

**The combined book beats the holdout and loses to mining.** The reason is the correlation: two universes sharing
**zero names** over the same days still move together at **+0.545**, because both are long US-equity momentum and
carry the same factor exposure. That is far too correlated for diversification to offset a holdout mean less than
half the mining mean. **This is why the arm was declared context in advance** — and it did not rescue the result
even on its own terms.

## 4. Predictions — all twelve

| | prediction | verdict |
|---|---|---|
| **P1** | S6's net > 0 | **CONFIRMED** — +3.187 |
| **P2** | *(load-bearing)* S6 clears BOTH nulls at p97.5 | **FALSIFIED** — fails both |
| **P3** | net below the in-sample +8.106 | **CONFIRMED** — +3.187 |
| **P4** | H4 fails, top trade > 10% | **CONFIRMED** — 30.0% |
| **P5** | neither arm passes; H4 the binding failure | **PART** — neither passes, but **four** hurdles fail, not one |
| **P6** | C9's GATE-ROT margin in SE smaller than S6's | **FALSIFIED** — C9 −6.9 is *closer* to clearing than S6's −10.7 |
| **P7** | era 2 above era 1 | **CONFIRMED** — +3.31 vs +2.98, though the in-sample gap of 11.6 bp collapsed to 0.33 |
| **P8** | gate open on 5–15% of bars | **CONFIRMED** — 9.4% |
| **P9** | *(principal)* annualised ≈16%, scored [12%, 20%] | **FALSIFIED** — +8.0% |
| **P10** | *(principal)* maxDD up slightly: > 3,158 bp, < 2× | **CONFIRMED** — 6,234 bp, 1.97× |
| **P11** | *(principal)* generalises lower: net > 0 and < +8.106 | **CONFIRMED** — +3.187 |
| **P12** | *(principal)* combined Sharpe > 0.887 | **FALSIFIED** — 0.716 |

**The principal's read on direction was right and mine on mechanism was wrong.** P11 and P10 land; the book did
generalise weakly with a somewhat worse drawdown. What neither of us predicted is that the *quality* would
collapse — P9 missed the magnitude by half, and nothing in the twelve anticipated two names to half the P&L.

## 5. RETIREMENT

**Both constructions are retired**, per §4 of the pre-registration: *"Any failure retires that construction."*

- **S6** — `mom_252_21` above rank 95 behind the nine-condition gate, hold above rank 90, 252-bar cap,
  equal-weight long, dollar-volume-weighted short. **RETIRED 2026-09-07.**
- **C9** — the same construction with the gate reduced to the index at a 252-bar high. **RETIRED 2026-09-07.**

**Neither enters `BOOK.md`.** The book remains **S1 and S2 only**, neither at capital.

**This does not license a search for a better construction followed by a second read.** The holdout is spent;
there is no untouched data left for this family. Any successor needs a new source of unseen data, and that is a
fixture question, not a strategy question.

**What is NOT retired:** the in-sample findings stand as measured — momentum's cross-sectional ranking cleared its
in-sample nulls at 143–164 SE (D369), six of nine gate conditions are logically entailed (D367), and the
symmetric winner-removal test cleared at 10.3 SE (D370). Those remain true *of the mining fixture*. What D371
establishes is that they did not travel.

## 6. Process failures in this read, recorded

1. **The first execution produced its evidence and then lost the JSON to a `KeyError` in the print loop.** A
   formatting typo destroyed the artifact of a one-shot, irreversible measurement. The runner now writes the
   result file **before** rendering anything. The re-run is bit-identical (deterministic per-draw seeds
   `[SEED, 371, arm, i]`) and reproduced `net +3.187, Sharpe +0.344, 561 trades` exactly, so it recovers the
   artifact of the read already spent — **the ledger is 1, not 2.**
2. **The console printed only each hurdle's verdict, never the null distributions.** Every other study this
   session printed the full table; the one that mattered most printed a boolean, so the loss at (1) was total
   rather than partial.
3. **Four failed attempts preceded the read**, all in universe construction — the audit hook refusing the
   holdout's metadata, `prep` asserting the mining fixture's F0 count, a floor share transcribed at six decimals
   against a 1e-9 tolerance, and a score cache that had never contained the strategy's own signal.
4. **`m_start` would have produced a confident, meaningless result** on a 65-bar sample with every check green
   (fixed in `ce2947c`). It was caught only because the score cache was also incomplete and forced a closer look.

## 6a. ADDENDUM, 2026-09-07 — THE DATA PARTITION IS CONFIRMED SOUND, and one hurdle is not

**The principal asked how each universe was chosen**, on the reasoning that if the mining set had been selected on
some characteristic, the holdout would be its systematically different complement and D371's failure would be a
partition artefact rather than a strategy failure. **It is not.** Audited from the builder and re-measured from
both fixtures.

**How the split was made.** `scripts/fetch_short_universe.py`: the eligible pool is sorted alphabetically — a
deterministic input — then shuffled **once** with `POOL_SEED = 20260828`. **Mining is `order[:3400]`** fetched,
1,573 after the screen; **the holdout is `order[3400:5100]`**, the next 1,700 of the *same permutation*, 803 after
the screen. Same seed, same eligibility rule, same per-symbol pre-live screen (252 bars, $1M/day, $3 floor, 126
minimum live bars), same span, same gates. The builder states the intent in terms: *"construction-identical by
design — no symbol enters or leaves because of anything learned since. A holdout on a differently-built fixture
makes a failure ambiguous, and ambiguity is the one thing a holdout must not produce."*

**The realised characteristics agree.** Measured on both fixtures, no strategy involved:

| | mining | holdout | ratio |
|---|---|---|---|
| price p25 / median / p75 | 23.54 / 42.66 / 77.62 | 22.68 / 43.78 / 83.78 | **0.96 / 1.03 / 1.08** |
| dollar volume p25 / median / p90 | 17.3M / 42.5M / 279M | 16.5M / 40.0M / 296M | **0.95 / 0.94 / 1.06** |
| median PUB half-spread | 28.65 | 28.58 | **1.00** |
| bars per name | 2,630 | 2,685 | **1.02** |
| `m_start` | 63 | 63 | **1.00** |
| **cross-sectional dispersion of `mom_252_21`** | 0.45 | 0.44 | **0.99** |
| names / eligible per bar | 1,573 / 704 | 803 / 369 | **0.51 / 0.52** |

Price, liquidity, spread, history length, and — most relevantly for a ranking strategy — **the dispersion of the
score itself** all match within a few percent. **The only material difference is size.**

**But size is not nothing, and it lands on two of the four failed hurdles.** The top 5% of eligible names is 35
in mining and **18** in the holdout; the book held **24.5 names in sample and 12.7 out of sample — half the
breadth**. Two hurdles are breadth-sensitive and were written as absolute counts:

- **H5 (≥10 names to half the P&L) is MIS-SPECIFIED, and this record says so.** At 12.7 names held, reaching ten
  names to half the P&L demands near-equal contribution from almost every position — a far harder bar than at
  24.5 names. It should have been stated relative to book breadth (names-to-half as a *share* of names held),
  not as a flat count. **The failure of H5 is therefore partly mechanical and should not be read at full
  strength.**
- **H4 (no trade above 10% of P&L)** leans the same way, less severely.

**The verdict does not rest on either.** H2 and H3 are size-neutral:

- **H2** compares net against rotation nulls computed *on the same universe*, so breadth cancels on both sides.
- **H3** is a per-trade statistic. **The 1% trimmed mean per trade at +63.9 against a 94.8 bp round trip — the
  average trade failing to cover its own costs — has nothing to do with how many names are held.**

**Conclusion: the partition is confirmed sound and the retirement stands on H2 and H3.** What the audit changes
is the weight H4 and H5 carry, and it identifies a hurdle specification to fix before any future read.

**Owed follow-up, not yet run:** the mining book restricted to a random half of its names, matched to ~803, to
measure how much of the H4/H5 failure is mechanical breadth and how much is out-of-sample decay. That is an
in-sample test and needs no holdout.

**One hazard found during the audit, unrelated to the result:** `V58.pct_of` memoises purely by score name, so a
process that touches both fixtures gets the **wrong percentile grid** back for the second. D371's read used one
fixture per process and was not affected; any future cross-fixture work must clear `_PCT` between re-points.

## 7. Files

`docs/decisions/D371-the-momentum-holdout-protocol.md` (pre-registration + addendum) ·
`data/d371_construction.json` (the frozen construction) · `scripts/run_d371_momentum_holdout.py` ·
`scripts/d371_build_holdout_scores.py` · `data/d371_read.json` (the read) ·
`temp/d371_rehearsal_mining.json` (rehearsal, not a result). Prerequisites: `d348_prep.py` (fixture-aware
expectations, `m_start`), `run_d365_momentum_buffer.py` (the guard's default-deny unlock).

**The holdout fixture has now been read once. `[HOLDOUT-GUARD]` logged every path opened:
`d290_scores_holdout.npz` ×2 and the probe.**
