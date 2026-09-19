# D562 RESULT — the forward slice is read and spent: the published trend book earned **+0.51 gross / +0.50 net** on 2024-01 → 2026-09, inside a null whose median is +0.18 and p95 +1.30, with the harness holding at ρ 0.73 against AQR — and on equities' worst days it **lost 1.29 σ, at the 5th percentile of random sign books**: a return component, not a hedge (disposition **B**)

*2026-09-19. Spec committed in `04ea121` BEFORE the runner and before any 2024+ session was read
(R8). Forward window **2024-01-02 → 2026-09-09** (696 sessions, 33 month-ends). Runner
`scripts/run_d562_trend_forward_read.py`, output `data/d562_trend_forward_read.json`, 57 s.
**The 2024+ slice of the futures fixtures is now spent for the trend line, for carry timing (D556
cell A, rebuilt here as a base), and for any assembled book that contains either.** Nothing
admitted (R15); the declared disposition rule places trend, and the placing is recorded below for
the principal's word.*

**Six of seven predictions held, and the one that missed missed on its magnitude clause.** The
book delivered what the in-sample excess and the literature said it would, the harness held out
of sample, the null is as wide as declared, and the shape prediction — that trend would be caught
on the wrong side of V-shaped equity selloffs — held, by far more than it was written for. This is
the second time in two records (D561 S3, now out of sample) that the "crisis alpha" reading of
this book failed at the declared bar; the first time it was a 0.02 σ miss, this time it is at the
5th percentile with the sign inverted.

---

## 0. What was read, and the one loader amendment

The fixture runs to 2026-09-09. From **2026-05-30 it carries weekend-dated BTC rows with up to 22
hourly closes** — CME's weekend crypto sessions, which did not exist when D555's loader was
written and which its guard (a weekend row with more than three closes is refused) correctly
stopped on. The forward loader drops them like every other weekend-dated row, so BTC's Monday
return spans the weekend exactly as every other root's does, and keeps D555's guard for every
other root and for BTC before that date. **The in-sample rows are asserted identical to D555's
loader's, row for row (118,214 rows), and the in-sample primary and D556's cell A reproduce their
artifacts to 1e-9 on the extended grid.** Extending the data did not move the past. Dropped rows:
27,431 placeholders, 70 stubs, 29 BTC weekend sessions.

## 1. The declared verdicts

| | observed | N1-full (3,546 offsets, purged 252) | |
|---|---:|---|---|
| **PRIMARY** — 12m published, forward gross Sharpe | **+0.512** (SE 0.53); Sortino **+0.711** | p05 −0.83, **p50 +0.18**, **p95 +1.30**, sd 0.65; rank **0.694** | **POSITIVE, INSIDE THE NULL** |
| Sortino | +0.711 | p50 +0.25, p95 +1.98; rank 0.68 | |
| N1-window (diagnostic, 193 offsets) | | p50 +0.25, p95 +1.49; rank 0.63 | agrees |
| **Harness** — monthly ρ with AQR TSMOM, 2024-01 … 2026-05 (29 months) | **+0.733** | | **HARNESS OK** |

| # | prediction | value | |
|---|---|---|---|
| P-1 | forward gross > 0; point +0.3; −0.5 … +0.9 | **+0.512** | **holds**, inside the interval |
| P-2 | inside N1-full p05 … p95 | rank 0.694 | **holds** |
| P-3 | Sortino ≥ Sharpe | +0.71 ≥ +0.51 | **holds** |
| P-4 | AQR ρ ≥ 0.5 | +0.733 | **holds** |
| P-5 | c5 on ES ≤ 0; point −0.1; −0.6 … +0.2 | **−1.291 σ** | **holds on sign, far outside the interval** |
| P-6 | c5 on carry A < 0 and below N1's p20 | −0.447 σ, rank 0.243 | **fails** on the rank clause; sign replicates |
| P-7 | dollar σ > $500 | **$10,920** | **holds** |
| P-8 | falsifiers | neither fires | |

**Disposition B, by the rule declared in §4 of the pre-registration:** P-1 holds and c5 on ES ≤ 0
→ *a return-component candidate for the personal book only, not a hedge, sized by vol target.*
Nothing enters `BOOK_PROP.md`; the vehicle fails C-d at every size measured. Admission to
`BOOK.md` is the principal's call, and the record's own view is in §5.

## 2. Performance — net and gross, the four groups

**12m published, forward:**

| | gross | net (turnover) | net incl. rolls |
|---|---:|---:|---:|
| Sharpe / Sortino | **+0.512 / +0.711** | +0.495 / +0.688 | +0.425 |
| ann. vol · total · max DD | 11.2 % · **+15.8 %** · **−21.7 %** | | |
| hit · skew · kurtosis | 51.7 % · −0.44 · 2.1 | | |
| turnover · cost | **23.4** weight-units/yr (in sample 14.7) → 18.2 bp/yr | | |
| breakeven | **24.5 bp/side** against ~1 modelled — cost is not the constraint | | |

**By year: 2024 +0.27, 2025 −0.31, 2026 (179 sessions) +2.03** with **+15.7 % of the +15.8 %
total**. The two full years net to nothing; the forward P&L is the first eight months of 2026,
which is the metals run and the equity rally: GC +5.0 %, SI +3.4 %, NKD +3.2 %, ES, NQ, RB the top
six; 6S −3.8 %, 6E −3.3 %, NG, HE the bottom four. Sectors: equities **+0.79**, commodities
**+0.80**, BTC +0.64, **fixed income −0.32, FX −0.58**. Twenty of 36 roots positive; **two roots
reach half the P&L**; top-1 / 3 / 5 share 32 / 74 / 107 %. Worst day 2024-08-02 (−3.9 %, SR3 on
the payrolls-and-yen Friday); best 2025-10-13 (+2.3 %, silver).

**Group 2 — root-months (1,188):** mean +1.33e-4, **median +1.99e-4** (the median is above the
mean this time — the body earned and the tails cost), win 52.3 %, payoff 1.02, skew +0.33.
Ex-top-1 % +0.19e-4, ex-bottom-1 % +2.27e-4, **symmetric trim +1.14e-4** (85 % of the mean). Top
1 % of root-months carry 86 % of the P&L: the same few-events structure as in sample.

**The CAP = 10 book read +0.549 / +0.768**, above the uncapped +0.512: the rates legs the cap
binds on lost on this slice (FI −0.32), so D561's in-sample monotonicity reversed. The gap is
0.04 on an SE of 0.5; it is noise, recorded because S2-P4 was a prediction.

**D556's carry A, rebuilt as a base: −0.563 / −0.821 forward**, 2025 alone −1.69. Carry timing
as published failed out of sample as it failed in sample; that slice is spent for it too.

**Group 4 — the nulls** are in §1. The null's median is +0.18 (a random persistent sign book on
these roots earned over 2024–2026, as it did over 2011–2023: the long tilt), and its width on 2.7
years is 0.65. The observed +0.51 is +0.33 above the null's median — the same excess as on both
in-sample windows (+0.37, +0.35). **Three windows, one excess, and no window on which it clears.**

## 3. The component line — and what it is made of

| | 12m dollar, 34 roots, forward | C-d-eligible sub-book (19 roots) |
|---|---:|---:|
| **C-a** net Sharpe / Sortino | **+0.709 / +0.955** (gross +0.727) | **−0.084 / −0.115** |
| **C-c** skew | **−1.52** | |
| **C-d** daily σ | **$10,920** — 21.8× the cap | **$1,782** — 3.6× the cap |
| total · max DD · hit | +$339,212 · −$195,030 · 52.9 % | −$6,571 |
| cost | $9,066: 1,350 sides + 1,436 roll sides | |
| N1-full on the net dollar book | p50 +0.07, p95 +1.33; rank 0.78 | |

The +0.71 is **three full-size contracts**: NKD +$125k, HO +$112k, RB +$79k, $315k of the $339k
total; the next is SI at +$29k, and the largest losers are 6S −$34k, PL, UB, ZB at −$15k each. The
sub-book that clears C-d is negative. **Not entered: fails C-c and C-d; C-a is three instruments.**
ρ with the ledger's live entry remains absent.

## 4. The overlay — the shape did not replicate, and inverted

| pair | ρ daily (in sample) | **c5** (hit) | null p05 / p50 / p95 · rank | c10 (rank) | DD ratio · null p50 · rank | Sharpe base → blend |
|---|---:|---:|---|---:|---|---:|
| **trend \| ES** | **+0.31** (−0.13) | **−1.291 σ** (18 %) | **−1.289** / −0.55 / +0.23 · **0.049** | −0.80 (0.08) | 0.822 · 0.817 · 0.51 | +0.95 → **+0.90** |
| trend \| 60/40 | +0.25 (−0.16) | −0.746 σ (26 %) | −1.03 / −0.47 / +0.35 · 0.22 | −0.64 (0.18) | 0.833 · 0.821 · 0.53 | +0.83 → +0.85 |
| trend \| carry A | −0.06 (+0.18) | −0.447 σ (38 %) | −0.93 / −0.09 / +0.57 · 0.24 | −0.04 (0.57) | 0.663 · 0.635 · 0.54 | −0.56 → −0.04 |

**Beside equities, on the forward slice, trend was the opposite of a hedge.** On ES's 34 worst
days it lost 1.29 σ of its own daily vol and was positive on six of them; that is below the 5th
percentile of the rotation null, whose median (−0.55) is the long tilt of a random persistent book
and whose 5th percentile is −1.289. In one of ES's five worst months was trend positive (April
2024, +1.6 %); March 2025 −1.2 %, March 2026 −0.6 %, June 2026 −1.5 %. The worst-day dates say
why: 2024-08-01/02/05, 2025-04-02 … 04-21 (seven of the 34), 2026-03-18 … 03-27 — **V-shaped
reversals**, where a monthly-hold book that is long equities and long metals into the drop is
caught, and reverses its signs at the month-end just as the market recovers. That is P-5's
mechanism, written before the read, and the magnitude was three times the point prediction. The
daily correlation with ES went from −0.13 in sample to **+0.31** forward. The vol-matched blend's
drawdown ratio (0.822) sits at the null's median (0.817): **exactly the diversification an
uncorrelated random book provides, and no more**, and the blend's Sharpe is below the base's.

D561's declared falsifier — "diversification, not convexity" — fired in sample by 0.02 σ and is
now confirmed out of sample at the 5th percentile with the sign reversed. **The 2020 and 2022 years
in D555 were sustained trends and this book paid in them; the 2024–2026 selloffs were reversals
and it paid for them.** Whether the next equity drawdown is one shape or the other is not something
this book knows, and a component that hedges one shape and amplifies the other is not a hedge.

Beside carry the sign of D561's tail finding replicates (−0.45 σ, hit 38 %) but at the 24th
percentile, not below the 20th; the two books' worst days still overlap more than a random book's
would, by less than in sample.

## 5. What the forward read settles, in the record's own view

- **The published construction is real and small on this universe.** Three windows, one excess of
  roughly +0.35 over a tilt-laden null, harness at 0.82 in sample and 0.73 out; AQR's own factor
  earned +0.93 on the same 29 months against this replication's +0.45 monthly, and the difference
  is universe (AQR's ~58 instruments, non-US indices and bonds this fixture lacks). If trend is to
  be held on this fixture it is as a vol-targeted return stream at roughly Sharpe 0.3–0.5 gross,
  whose P&L arrives in a few months of a few years, and which the programme's null cannot
  distinguish from a random persistent book on any window it has.
- **It is not a hedge, and should never be sized as one.** The convexity claim has now failed
  twice, the second time badly. Any book that holds it must survive its worst days beside
  equities' worst days.
- **It has no prop vehicle.** σ $10,920 at minimum size; the C-d-eligible sub-book is negative in
  sample and out.
- **Disposition B stands as declared**: return-component candidate for the personal book only.
  The record recommends the principal treat "candidate" literally — a line in `BOOK.md`'s
  standards to be met, not an entry — and notes that the personal book's admission standard for a
  monthly-hold futures stream has not been written.
- **Spent:** the 2024+ slice for trend, for carry timing, and for any assembled book containing
  either. The lines that do not contain them keep it.

## 6. What was not done, and what is still wrong with this

- **2.7 years is 33 month-ends.** Every forward statistic here has an SE near 0.5 and the null a
  width of 0.65; the read settles the sign, the shape and the harness, not the magnitude.
- **A name-randomised null** would separate the rotation null's tilt (its median of +0.18 on the
  Sharpe and −0.55 on ES's worst days) from timing; not run here or in D561.
- **The 2026 partial year is 179 sessions**, ends 2026-09-09, and carries the whole forward P&L;
  the per-year table says so and the record does not read it as a trend.
- No overlay on the ledger's live arm, whose daily P&L is not on disk.
- The three audits, the loader identity, the two artifact reproductions, the worst-day audits, the
  exactness guard and the rotation-semantics check are in the json's `audits` and `harness`.
