# Conflict register — all 51 cross-lane IDs, one line each

[← index](../00-INDEX.md) · siblings: [vs repo](02-versus-repo-measurements.md) · [agreements](03-agreements.md) · [inside briefs](04-inside-briefs.md)

**CONFLICTS ARE RECORDED, NOT ADJUDICATED.** Standing instruction from the principal, 2026-09-10.
Every reading below stands; an agent's preference is reported **as that agent's preference**. This
file is a **lookup table**, not a summary — each row links to the record that holds the full readings.

**ID scheme.** `C` = campaign 1 (rounds 5–6). `D`/`E`/`F`/`G` = `Scan-100926` rounds 1/2/3/4.
Later rounds never renumber earlier IDs, so an ID is stable.

| status | meaning |
|---|---|
| ● | still open, both/all sides stand |
| ◐ | a later lane supplied a mechanism or a primary source; **both readings still stand** |
| ▲ | touches a repo measurement → [vs repo](02-versus-repo-measurements.md) |

---

## `C1`–`C17` — campaign 1 · [selection §11](../../the-selection-round.md) · [reversal §10](../../the-reversal-round.md)

| | | topic | status |
|---|---|---|---|
| `C1` | tick-size/access-fee amendments: delayed to Nov 2027 · Nov 2026 · **stayed, not delayed** | [data](../data/00-index.md) | ● |
| `C2` | MEMX first trading day: 2020-09-21 vs 2020-09-29 | venue history | ● |
| `C3` | Bats→Cboe rename effective: 2017-10-16 vs 10-17; Delaware date in no primary source | venue history | ● |
| `C4` | NYSE Alternext→Amex: 2009-03-18 vs 2009-03-03 — **two primary sources disagree** | venue history | ● |
| `C5` | is there a published daily autocorrelation for an EW US portfolio? none citable vs one from 1964–93 | [nulls](../method/02-nulls-and-block-length.md) | ◐ → `C17` |
| `C6` | the vendor's daily adjustment basis: **its API docs contradict its own support FAQ** | [fixture defects](../data/04-fixture-and-vendor-defects.md) | ● ▲ |
| `C7` | what is wrong with Corwin–Schultz: **understates** vs **fabricates high/low** | [spread](../cost/01-spread-estimation.md) | ● ▲ |
| `C8` | fixture bar count 4,187 vs 4,191 | [vs repo R8](02-versus-repo-measurements.md) | ● ▲ |
| `C9` | doubled day at the ex-date transitions: a doubled **ex-date** vs a doubled **settlement** date | [corp actions](../data/03-corporate-actions-and-splits.md) | ● |
| `C10` | declared ex-dividend holes: one (2017-09-05) vs **two** (+ 2024-05-28) | [corp actions](../data/03-corporate-actions-and-splits.md) | ● |
| `C11` | anomaly survival rate **35% vs 85%** — `K6` weights neither, because neither applies costs | [replication](../method/03-replication-and-multiple-testing.md) | ● |
| `C12` | is the surviving return in the short leg? different **statistics AND samples** | [long vs short](../signals/02-long-leg-versus-short-leg.md) | ● |
| `C13` | cost levels: FIM vs NMV — `K6` resolves it by quoting one side's own text on **patient** traders | [what anomalies pay](../cost/02-what-anomalies-pay.md) | ◐ |
| `C14` | months-positive for the EW bias: **99.2% vs 92%** | [EW bias](../cost/04-equal-weight-bias.md) | ● |
| `C15` | EW bias magnitude: **36.4 vs 12.67 bp/month** — different universes and eras | [EW bias](../cost/04-equal-weight-bias.md) | ● |
| `C16` | two coefficient signs in the EW-bias literature come out **backwards** vs two prior papers, per the authors' own text | [EW bias](../cost/04-equal-weight-bias.md) | ● |
| `C17` | daily EW autocorrelation: none citable · one 1964–93 figure · **a modern one, +0.01 to +0.06, indistinguishable from zero 2001–08 with the significant values NEGATIVE** | [nulls](../method/02-nulls-and-block-length.md) | ◐ ▲ |

**Recorded as NOT a conflict:** `K3`'s *"item-code absorption is small"* against `J1`/`J2`'s 36–68%
text-level absorption — **the events those lanes measured carry no item code at all.** Different
objects, different granularity. Neither displaces the other.

## `D1`–`D10` — `Scan-100926` round 1 · [record §4](../../Scan-100926/R1-99-record.md)

| | | topic | status |
|---|---|---|---|
| `D1` | **does the long leg pay?** `A3` Var(t) 0.98 vs `A2` 1.35–1.81 — **the benchmark is the crux** | [long vs short](../signals/02-long-leg-versus-short-leg.md) | ● ▲ |
| `D2` | what does the `$5` screen cost? cuts short-leg alpha 77% vs costs ~23% of the median premium | [the floor](../cost/03-price-floor-and-screens.md) | ● ▲ |
| `D3` | `acceptanceDateTime` defect rate: 58% · 62.7% · 9% · **40.2% then 0% — the first reading with a MECHANISM (era-dependence)** | [timestamps](../data/02-filing-text-and-timestamps.md) | ◐ |
| `D4` | does SEC ignore `Range` headers? flatly yes vs **path-dependent** | [filing text](../data/02-filing-text-and-timestamps.md) | ● |
| `D5` | the 35%/85% replication split: weights neither vs reaches its own view | [replication](../method/03-replication-and-multiple-testing.md) | ● |
| `D6` | the canonical low-turnover survivors: eight vs **five of the eight negative or zero in 2010–2024** | [decay](../signals/04-decay-and-era.md) | ● |
| `D7` | `A3`'s five internal conflicts — incl. a supportive paper that cannot reject 50/50, and an optimal short weight of **30%, not zero** | [long vs short](../signals/02-long-leg-versus-short-leg.md) | ● |
| `D8` | one paper disagreeing with itself: **draft and published abstracts differ in SIGN** | [tooling](../method/04-tooling-hazards.md) | ● |
| `D9` | is the cheapest candidate reachable? *"only a split-adjusted share count"* vs **no split history in XBRL** — a **dependency failure**, not a contradiction | [share count](../signals/06-share-count-and-issuance.md) | ◐ |
| `D10` | does as-filed data weaken a result? **no — the accruals hedge pays 0.673%/mo as-filed against 0.296% and insignificant on the vendor's** | [XBRL](../data/01-sec-xbrl-fundamentals.md) | ◐ |

## `E1`–`E11` — round 2 · [record §4](../../Scan-100926/R2-99-record.md)

| | | topic | status |
|---|---|---|---|
| `E1` | what does CFM attribute the long-leg advantage to? SMB from the 2×3 construction vs **SMB only under the benchmark Blitz refused** | [benchmark](../method/01-benchmark-choice.md) | ● |
| `E2` | is `Var(t) = 0.98` an absent signal or a **benchmark artefact**? mismatch predicts 0.76–1.19 | [benchmark](../method/01-benchmark-choice.md) | ● |
| `E3` | does `CbOP` survive or is it subsumed? `t` 3.02–3.44 vs **subsumed, t 6.99 vs 0.42** — and both sides are interested parties | [profitability](../signals/01-profitability-family.md) | ● |
| `E4` | a paper's **Table 3 against its own prose** on whether gross profitability nets positive | [profitability](../signals/01-profitability-family.md) | ● |
| `E5` | is "no filers" a `0` or an `HTTP 404`? two censuses of the same tag-years — **every other cell matches exactly** | [XBRL](../data/01-sec-xbrl-fundamentals.md) | ● |
| `E6` | weighting: three positions, three justifications; capped value weights worth **+8.5pp** on replication | [construction](../signals/03-construction-dispersion.md) | ● |
| `E7` | do long legs dominate? Sharpe **1.10 vs 0.69** vs *"the no-short recommendation is not robust"* | [long vs short](../signals/02-long-leg-versus-short-leg.md) | ● |
| `E8` | is there split history in XBRL? none vs **a tag carried by 2,280 CIKs** — then rejected on five measured defects | [splits](../data/03-corporate-actions-and-splits.md) | ◐ |
| `E9` | does the reference dataset divide or multiply by the split factor? **docs say `shrout/cfacshr`, the shipped code says `shrout*cfacshr`** — an inverted factor turns a 7:1 split into a 49-fold error | [splits](../data/03-corporate-actions-and-splits.md) | ◐ |
| `E10` | does composite equity issuance need a share count? **a primary source says splits leave it unchanged**, and the reference code takes none | [share count](../signals/06-share-count-and-issuance.md) | ◐ |
| `E11` | does "latest filed wins" reconstruct a vintage? PIT-reconstructible vs **one instant reported as both 717,376,170 and 3,600,000 — wrong by 199×** | [XBRL](../data/01-sec-xbrl-fundamentals.md) | ◐ |

## `F1`–`F7` — round 3 · [record §4](../../Scan-100926/R3-99-record.md)

| | | topic | status |
|---|---|---|---|
| `F1` | **THE CAMPAIGN'S CENTRAL CONFLICT.** Does an EW profitability long leg beat its own EW universe? **`C3` +0.026 [t 0.45]** vs **`C4` +0.405 [t 3.00]** — same era, both fully controlled | [long vs short](../signals/02-long-leg-versus-short-leg.md) | ● ▲ |
| `F2` | does the lagged deflator kill gross profitability? **annual yes** (t → 1.04–1.85) · **quarterly no** (0.51, t 3.40) · **post-2014 no** — a scope finding, all three stand | [profitability](../signals/01-profitability-family.md) | ◐ |
| `F3` | which assets does *Deflating profitability* deflate by? three second-hand restatements said **lagged**; the lane that **obtained the paper** says **CURRENT**, and the code comment agrees | [profitability](../signals/01-profitability-family.md) | ◐ |
| `F4` | is the FF profitability spread alive post-2013? **zero in every size quintile but the largest** vs **alive and widening** — same lane, two datasets | [decay](../signals/04-decay-and-era.md) | ◐ |
| `F5` | how large is post-publication decay? the founding paper's **drafts: 10%/35%** · its **publication: 26%/58%** | [decay](../signals/04-decay-and-era.md) | ● |
| `F6` | decay or era? *"partly explained by a general time trend"*, and the worst five-year blocks **pre-date** publication | [decay](../signals/04-decay-and-era.md) | ● |
| `F7` | a paper's stated conclusion **flips the sign of its own table's median**, and one winsorization choice swings 9% → 53.5% between draft and publication | [construction](../signals/03-construction-dispersion.md) | ● |

## `G1`–`G6` — round 4 · [record §4](../../Scan-100926/R4-99-record.md)

| | | topic | status |
|---|---|---|---|
| `G1` | does a quarterly sort survive the one-quarter-lagged deflator? **read from a published table: 0.51 [t 3.40]** vs **its own measurement: 0.163 [t 1.43], three for three** | [profitability](../signals/01-profitability-family.md) | ● |
| `G2` | is winsorise-vs-trim arbitrary? yes for a **regression**; **provably not for a SORT** — winsorising moves 0 of 2,612 names while trimming turns over 8.9–79.4% | [construction](../signals/03-construction-dispersion.md) | ◐ |
| `G3` | is `C4`'s own-universe benchmark correctly built? the conditional is right, but **on NYSE breakpoints the same shortcut is 13.6 bp/month and flips the sign** — one of two things that would settle `F1` | [benchmark](../method/01-benchmark-choice.md) | ● |
| `G4` | is pure factor timing worth anything? **Sharpe 0.71, never costed** vs *"meagre"*, break-even 1.8 bp/dollar, *"de minimis"* | [arrival](../signals/05-arrival-and-drawdown.md) | ● |
| `G5` | **an unexplained control**: two of a reference library's own six published information ratios fail to reproduce, **one sign-reversed**, after ruling out vintage, convention and language | [replication](../method/03-replication-and-multiple-testing.md) | ● |
| `G6` | **three more documentation-versus-code disagreements, all with the code right.** With `E9` and `F3` the class is **five instances and should be assumed, not discovered** | [tooling](../method/04-tooling-hazards.md) | ◐ |

---

**`D1`–`D10`, `E1`–`E11`, `F1`–`F7` and `G1`–`G6` ALL STILL STAND.** `F2` is directly affected by
`G1` and both are open. `D9` is recorded as *answered* by `B4` — **and under [R15](../../../RULES.md#r15)
only the principal closes an avenue.**
