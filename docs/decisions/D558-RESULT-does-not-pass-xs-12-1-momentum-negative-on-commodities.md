# D558 RESULT — **DOES NOT PASS**: cross-sectional 12-1 momentum as published is **−0.26 gross** on the 17 commodities over 2016–2023, at the 35th percentile of its own null; the short leg loses in every era, the loss is the energy complex, and the worst month is the May 2020 crude rebound against a short leg built on the April crash

*2026-09-19. Spec committed in `60aa4fc` BEFORE the runner (R8). Primary window 2016-01-04 →
2023-12-29 (2,063 sessions on the 17-root grid; the two Good Fridays 2021-04-02 and 2023-04-07 on
which no commodity printed are the only sessions absent against D555's 2,065); long window
2011-01-03 → 2023-12-29 (3,349 sessions) as the declared diagnostic; **the 2024+ slice was not
read** (`last_session_read` 2023-12-29, `reserved_from` 2024-01-01). Nothing admitted (R15).
Nothing closed. Runner `scripts/run_d558_xs_momentum.py`, output `data/d558_xs_momentum.json`,
21 s (the enumerated null: 5.3 ms an offset, 2,062 offsets × 3 cells, projected 11 s, took 12).*

**The construction ran as pre-registered and the effect is absent, with the sign against it.**
Ranked on the 11 calendar months ending the month before, long the top third, short the bottom
third, equal weight, held a month: the published equal-weight book returns **−0.259 gross** (SE
0.31) on 2016–2023, **−0.20** over 2011–2023, and sits **below the median** of a purged rotation
null whose p95 is +0.71. Four of seven predictions held — the ones about the sort's *relation to
trend* (ρ 0.62 with the CM time-series book), its *legs* (the long leg out-earns the short), its
*crash* (May 2020 is a reversal month for both books) and its *vehicle* (the dollar book fails C-d
at $5,236 a day). The ones that inherited a magnitude did not, and **P-5 failed in a direction
that is itself the finding**: the vol-scaled cell reads −0.03 against the equal-weight −0.26,
because vol-scaling halves the weight on the five energy roots, and the energy roots are where the
whole loss lives.

---

## 1. The declared verdict

| | | |
|---|---|---|
| **PRIMARY** — cell (1) EW/published, gross Sharpe 2016–2023 | **−0.259** (SE 0.31) | N1 purged: p05 −0.71, p50 −0.10, **p95 +0.70**, rank **0.354** → **INSIDE, below the median** |
| **N2 family**, 3 declared cells | best **+0.052** (dollar, net) | p50 −0.00, p95 +0.77, rank 0.56 → **INSIDE** — the family's best is the null's median, as in D555 and D556 |

N1: 2,062 offsets enumerated, `purge_sessions` 252, **1,560 after the purge**, SE 0 by enumeration.
The exactness guard held on 20 offsets (bit-identical to the plain loop; rotated leg sizes are the
observed ones). The purge matters here as it did in D555: the un-purged p95 is +1.69 and the
un-purged maximum +2.24 sits at k = 1,824 = L − 239, a sign read 239 sessions into the future.

| prediction | | |
|---|---|---|
| **P-1** primary > 0, above N1 p95; deposit 0.15–0.35 net, judged gross 0.17–0.37 | **−0.259** gross, −0.268 net; p95 +0.705 | **fails** |
| **P-2** daily ρ with the CM-restricted 12m TSMOM book in (0, 0.7) | **+0.624** (monthly +0.578) | **holds** — related, not the same object |
| **P-3** long leg's mean root-month contribution > short leg's | **+2.9e-4** vs **−7.7e-4** | **holds** — the short leg is the loss |
| **P-4** worst month is a reversal month (CM TSMOM also < 0) | **2020-05: −9.89%**; CM TSMOM **−5.05%** | **holds** |
| **P-5** vol-scaled within ±0.15 of EW | **−0.030** vs −0.259, Δ 0.23 | **fails** — see §3 |
| **P-6** dollar book fails C-d | σ **$5,236** a day | **holds** |
| **P-7** falsifier: gates green and primary below N1 p50 | gates green; −0.259 < −0.098 | **fires: the sort did badly on this window**; nothing about the fixture is implicated |

## 2. Performance — net and gross, the four groups

**Cell (1), EW/published (0.5 × (EW long − EW short), dollar-neutral in weight), 2016–2023:**

| | gross | net (turnover) | net incl. rolls |
|---|---:|---:|---:|
| Sharpe | **−0.259** (SE 0.31) | −0.268 (SE 0.31) | −0.299 |
| ann. vol · total · max drawdown | 12.8% · −27.2% over 8 years · **−48.0%** | | |
| hit (days) · skew · kurtosis | 51.0% · −0.30 · 3.9 | | |
| turnover · cost | **4.75 weight-units/yr** → 11.5 bp/yr at the modelled ~1 bp/side | | |
| breakeven cost | **negative** (−70 bp/side): there is no cost at which this book is positive | | |

Long window 2011–2023 gross **−0.201**. **Cell (2), vol-scaled/published:** gross **−0.030** (SE
0.31), net −0.044, ann. vol 15.6%, max drawdown −46.3%, hit 51.2%, skew −0.24, turnover 9.19
weight-units/yr (21.4 bp/yr); mean net weight **+0.045** — the book is net long in weight space, as
declared it would be; long window −0.060. **Cell (3), dollar at minimum size, net:** +0.052 (SE
0.28), gross +0.068, §4.

**Eras** (primary series): 2011–2015 **−0.06**, 2016–2019 **−0.65**, 2020–2023 **−0.00**. **Years**: 2012
−1.08, 2013 +0.95, 2014 +0.06, 2015 −0.01, **2016 −1.21**, 2017 +0.85, 2018 −1.01, 2019 −0.68, 2020
−0.27, 2021 −0.69, **2022 +0.99**, 2023 −0.33 — **two of eight primary years positive**, and the
best months are five of the first seven of 2022 (long energy into the Ukraine rally: +7.5%, +7.3%,
+8.7%, +7.4% in January, March, April, May) plus July 2020.

**Group 2 — root-months (1,124 on the primary holds, in units of book return: the root's weight ×
its return summed over the holding month; the contributions sum to the book total exactly):**

| | n | mean | median | ex-top-1% | ex-bottom-1% | symmetric trim | win | payoff | skew |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **combined** | 1,124 | **−2.42e-4** | −0.52e-4 | −5.64e-4 | +1.06e-4 | **−2.15e-4** | 49.5% | 0.94 | −0.43 |
| **long leg** | 562 | **+2.87e-4** | +4.57e-4 | −0.24e-4 | +6.93e-4 | +3.82e-4 | 52.7% | 0.99 | −1.07 |
| **short leg** | 562 | **−7.72e-4** | −5.22e-4 | −11.45e-4 | −4.37e-4 | −8.11e-4 | 46.3% | 0.88 | +0.21 |

The symmetric trim moves the combined mean by 11%: the loss is the body, not a tail. The long leg
earns +0.29 bp a root-month in book units and the short leg loses 0.77 — the sort's short leg is
where the 2016–2023 commodity market's rebounds land, and it is the leg the deposit's own failure
note names ("sharp reversals after prolonged trends destroy the short leg").

**Group 3 — what the losers depend on.** The total is negative (−0.272), so the shares are of the
loss: **RB alone is 64% of it** (−0.175; roots to reach half the loss: **one**), the five worst
(RB, BZ, CL, ZM, HE) are 163% and the ten worst 210%, offset by the six roots that earned — PA
+0.106, SI +0.068, ZL +0.056, HG +0.042, ZS +0.027, GC +0.012 (metals and oilseed). **Six of 17
roots positive.** Held-session Sharpe per root: RB −0.75, ZM −0.54, HE −0.37, BZ −0.35, ZW −0.35,
ZC −0.35, CL −0.27; ZL +0.64, HG +0.47, PA +0.46, SI +0.42, ZS +0.35.

**The energy complex is the whole loss, and that is a property of the construction (diagnostic,
unpromotable).** The five energy roots (CL BZ HO RB NG) contributed **−0.390** of the −0.272 total —
ex-energy the book is **+0.118** (Sharpe +0.19 against −0.40 for the energy legs). They sit in the
**same leg on 56 of 96 month-ends (all five on 35)**: a third-of-17 sort with a five-name block that
moves together is, most months, an energy-versus-everything bet, and with 6/6 legs that block is
most of one leg. That is also why P-5 failed: cell (2)'s vol scale gives an energy root a mean
weight of 0.094 against 0.161 for the rest, halves the bet, and lifts the Sharpe by 0.23 without
changing a single sign.

**Eligibility, as declared and as it ran:** on the 96 primary holds, 17 eligible on 75 month-ends,
16 on 8, 15 on 10, 14 on 2, 10 on 1 (2021-01-29); legs 6/6 on 83, 5/5 on 12, 4/4 on 1; **boundary
ties 0; flat months 0** (the 18 flat month-ends are all warm-up, 2010-06 through 2011-11). HE and LE
ineligible on 17 month-ends each, ZC 3, the other grains 1, everything else 0 — D555's 240-return
floor on day-session roots whose front-change return is undefined, as the pre-registration said.
The 1-month cell's own floor would have voided 277 root-months; the no-floor sum is bit-identical
to the floored read on all 2,275 cells where that one is finite.

**Group 4 — the nulls** are in §1. The offset profile of the primary (mean null Sharpe by shift of
the membership, in sessions): +1 … +21 **−0.32**, +21 … +63 −0.19, **+63 … +126 +0.49**, +126 … +252
−0.07, **+252 … +504 −0.52**, +504 … +1,000 +0.20, +1,000 … +1,559 −0.22, and on the contaminated
side (−252 … −21) **+1.63**. A membership lagged three to six months earns; lagged one to two years it
loses — the same persistence-then-reversal shape D555 found on the time-series sign, now on a
cross-sectional membership, and no purge band takes the observed out of its null.

## 3. Comparability — the sort against the time-series book on the same 17 roots

D555's 12-month time-series momentum book restricted to the commodities, rebuilt in-process on
this grid, scores **−0.056** on 2016–2023 (D555's own per-sector figure: −0.056; the 3e-5 difference
is the two Good-Friday zero-return sessions in D555's series). The sort correlates with it at
**ρ = 0.62 daily, 0.58 monthly**: the deposit's "1 ≈ 4" is about right, and the sort is the worse
of the two here by 0.20 of Sharpe. **The worst month, named:** membership set 2020-04-30 after the
April crash — short CL (11-month read −1.18), RB (−1.25), BZ (−0.99), HO (−0.74); long PA, ZW, GC,
ZM, ZS, SI. In May the June crude contract rose **+74%** same-contract, RB +34%, BZ +40%, HO +18%:
the four energy shorts cost −4.9, −2.6, −3.0 and −1.6 points of a **−9.9%** month, and SI's +23%
on the long side gave back only +1.7. The next-worst (Nov 2021, −6.4%) is the mirror: long all five
energy roots at 11-month reads of +0.48 to +0.81, crude −18.5% in the month. April 2016 (−4.9%) is
May 2020 in miniature. **Three of the five worst months are the energy block reversing against
the sort**, and the CM time-series book lost in each of them too.

## 4. The component line — the dollar book decomposed first

One minimum-size contract per positioned root, **16 roots** (BZ ranked, its slot untraded), 11.7
contracts held on average, $3/$6 a round trip + one tick, a roll two sides, 2016–2023, **by root
before anything is quoted**:

| root | size | net $ | σ/contract/day | | root | size | net $ | σ/contract/day |
|---|---|---:|---:|---|---|---|---:|---:|
| **PA** | full | **+133,204** | **4,344** | | CL | MCL | −2,924 | 161 |
| HO | full | +17,853 | 2,387 | | NG | MNG | −3,602 | 148 |
| ZL | full | +14,370 | 511 | | PL | full | −7,033 | 805 |
| SI | SIL | +13,214 | 368 | | ZC | full | −7,339 | 381 |
| ZS | full | +12,402 | 761 | | HE | full | −8,394 | 609 |
| HG | MHG | +3,823 | 114 | | LE | full | −9,580 | 510 |
| GC | MGC | +1,064 | 147 | | ZW | full | −13,697 | 671 |
| | | | | | ZM | full | −23,598 | 550 |
| | | | | | **RB** | full | **−84,463** | **1,956** |

**Net total +$35,298; the top contributor is palladium at 377% of it**, and the largest loser is
RB at −239%. The σ per contract runs **$114 (MHG) to $4,344 (PA)** — a 38× range — so the book is,
as D556's was, a bet on whichever full-size contracts carry the largest dollar σ, and its +0.05
sign disagrees with the equal-risk book's −0.26 for that reason alone.

| | dollar, 16 roots | C-d sub-book (CL GC HG NG SI ZC) |
|---|---:|---:|
| **C-a** net Sharpe | **+0.052** (SE 0.28); gross +0.068 | +0.062 (SE 0.32); gross +0.090 |
| hit · **C-c** skew · kurtosis | 52.6% · **−0.51** · 15.0 | 50.4% · −0.76 |
| **C-d** daily σ | **$5,236** — 10.5× the cap | **$529** — the six roots that clear C-d individually do not clear it together |
| total · max DD · cost | +$35,298 · −$168,160 · $10,770 (1,762 sides, **1,506 of them rolls**) | +$4,235 · −$27,124 |
| ρ with the ledger's live entry | **ABSENT** — the MACD arm's per-session P&L is not on disk | |

**Not entered: fails C-a, C-c and C-d; C-e provenance is this record.** The vol-scaled dollar cell
is the same object (one contract is one contract), as the pre-registration said.

## 5. Against the deposit's document

`PUBLISHED_STRATEGIES.md` §5 discounted the 10.14% published alpha to an expected net Sharpe of
0.15–0.35 and called the sort "the weakest of the five as a standalone." On these 17 roots and
this window it is **−0.27 net**, below its null's median, and the sibling time-series book on the
same roots is −0.06: neither expression of commodity trend earned on 2016–2023, and the
cross-sectional one earned less because its short leg is structurally the rebound leg. The
document's *character* claims held — the two are strongly correlated (0.62), the short leg is the
crash exposure, and the deposit's own multiple-testing note about the source is, on this
evidence, the right instinct. Its magnitude did not, for the third study running.

## 6. What was not done, and what is still wrong with this

- **No sweep of ranking or holding period** (the source's 32 pairs), no tercile other than
  ceil(n/3), **no sector neutralisation** — the energy-block finding of §2 says a sector-neutral
  or sector-capped sort is the different construction the numbers point at, and it is a new
  pre-registration, not an amendment.
- **No term-structure conditioning**: Miffre–Rallis's "momentum profits concentrate in backwardated
  markets" is the double sort, a separate record.
- **D555's 240-return floor removes the livestock from a sixth of the primary month-ends** because
  a day-session root's front-change return is undefined on this fixture. That is the declared rule
  applied as written; a fixture that carried a day-session open would remove the artefact.
- **The published construction is equal-weight and unlevered; cell (2) is not dollar-neutral** (mean
  net weight +0.045). Neither cell is a vol-targeted book and no cap was applied.
- **The long-window null was not enumerated**, as in D555 and D556; the long-window Sharpe is −0.20
  and it would not change the verdict.
- The four audits ran and each was proven to raise (json `audits`: the lag audit on the unlagged
  book, the sign audit on the negated and on the mis-lagged grid, the right-quantity audit on a daily
  grid, the new leg-membership audit on a swapped long/short pair; 1,702 membership cells checked
  against the independent pandas path).
