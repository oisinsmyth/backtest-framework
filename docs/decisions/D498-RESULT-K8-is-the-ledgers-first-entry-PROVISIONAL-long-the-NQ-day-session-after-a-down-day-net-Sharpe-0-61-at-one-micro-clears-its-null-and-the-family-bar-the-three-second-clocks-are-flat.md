# D498 RESULT (in-sample) — K8 is the ledger's first entry, PROVISIONAL: long the NQ day session after a down day, net Sharpe +0.61 at one micro, clears its own null and the family bar; the three second-clock cells are flat

**In-sample result of D498.** Runner `scripts/run_d498_k8_and_second_clocks.py --run`
(`--selftest` passes; 0.1 min), artefact `data/d498_k8_second_clocks.json`, trade files per root
and cell. NQ and ES, 1,993 full sessions each, **2016-01-04 → 2023-12-29; 2024+ unread** (the
forward read of K8 is a guarded command, not run under this record).

## 0. The numbers

| intraday, one micro, $3 | trades (share) | gross $/trade | bp (SE) | other side, bp | diff z | hit | skew | MAE p50 / p95 / worst | net Sharpe (SE) | N1 p95 | sub-periods bp | verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---|---|
| **NQ K8** long the day session after a down day | **871 (43.7%)** | **+17.87** (median +20.50, trimmed +18.16) | **+11.6 (4.0)** | −3.1 (after up days) | **+2.89** | 56.9% | −0.02 | −92 / −560 / −1,144 | **+0.61 (0.32)** | +9.1 ✓ | +14.6 / +6.0 | **PROVISIONAL entry** |
| ES K8 (check root) | 870 | +5.68 | +4.9 (3.0) | +0.7 | +1.07 | 55.1% | −0.07 | −62 / −352 / −618 | +0.18 (0.35) | +6.4 ✗ | +4.3 / +3.8 | below C-a |
| NQ E1 turn-of-month | 364 (18.3%) | +11.23 | +6.9 (6.2) | +3.7 | +0.46 | 55.8% | −0.23 | | +0.22 (0.33) | +12.7 ✗ | +7.0 / +5.9 | closed |
| NQ E2 FOMC 09:30 → 14:00 | 63 (3.2%) | +9.28 | +2.8 (5.8) | +2.4 | +0.06 | 41.3% | +0.51 | | +0.18 (0.35) | +21.7 ✗ | −3.0 / +11.4 | closed |
| NQ E3 first-30 fade at 15:30 | 1,989 | +0.67 | +0.4 (0.8) | (its negative) | +0.48 | 48.6% | +0.76 | −24 / −140 / −460 | −0.53 (0.32) | +1.2 ✗ | −0.6 / +1.2 | closed |
| ES E1 / E2 / E3 | 364 / 63 / 1,965 | +6.54 / +3.41 / −0.08 | +5.2 / +2.8 / +0.7 | | +0.54 / +0.25 / +1.00 | | | | +0.15 / +0.02 / −0.94 | | | closed |

**Family maximum of the difference z** (8 cell-roots, 1,991 common offsets): p50 +1.22, p95
**+2.41**, p99 +3.01. **Observed maximum +2.89 (NQ K8); 1.5% of offsets reach it.** No day below
−2% of a $50k account at one micro in any cell. Correlations on NQ: ρ(K8, the ungated day
session) +0.70; ρ(E1, K8) +0.32; ρ(E2, K8) +0.08; ρ(E3, K8) −0.02.

## 1. K8, read honestly

**What it is.** On 44% of sessions, about twice a week, long one MNQ from the 09:30 open plus a
tick to the 15:59 close, when yesterday's day session closed below its open. Gross +$17.87 a
trade against $3, median +$20.50 and a symmetric trim of +$18.16 (the mean is not a tail), hit
57%, skew flat, positive in 6 of 8 years (2018 −12 bp and 2022 −4 bp the exceptions) and in both
sub-periods (+14.6 bp in 2016–2020, +6.0 in 2021–2023). Net Sharpe **+0.61 (SE 0.32)** at one
micro on the session calendar. The day session after an **up** day is −3.1 bp on the other
side, so the difference is +14.7 bp at z +2.89, above the family p95 of +2.41 with 1.5% of
common rotations reaching it.

**What the entry is, and is not.** It is **PROVISIONAL** by D498's own rule and by the ledger's:
C-a (0.61 > 0.5 on the point estimate), C-c (skew −0.02), C-d (daily σ well under 1% of the
account) pass; **the provenance is selection** — the cell was seen as D495's control before it
was declared — and no in-sample bar, including the family one it clears here, substitutes for
the forward read that provenance requires. The SE of 0.32 says the in-sample Sharpe is between
0.3 and 0.9 at one standard error. ES shows the same sign at less than half the size (+4.9 bp,
Sharpe +0.18), inside its null; the two roots move together (ρ ≈ 0.85 on the day session), so
ES is a weaker expression of the same thing, not an independent confirmation.

**The mechanism, as far as the record goes.** This is a one-day reversal of the day session on
the Nasdaq index, long only, and the record has three things on it: D487's day-session
autocorrelation on NQ (−0.087, outside its rotation band), D495's top-decile fade (which turned
out to be this effect on a subset), and the literature's daily index reversal (Della Corte,
Kosowski, Wang: overnight-intraday reversal across index futures; the periodic-closure model).
The short side is dead here as everywhere on this index: the day session after an up day is
−3.1 bp, not enough to pay for anything.

## 2. The second clocks

**All three are closed, and two of the three were the literature's.** Turn-of-month on NQ is
+6.9 bp a day on 46 days a year, hit 56%, but its other side is +3.7 bp and the difference is
z +0.46: the turn-of-month days are the ordinary drift plus a little, inside the null. The
pre-FOMC drift to 14:00 is +2.8 bp on 63 days, hit 41%, z +0.06 — as the post-2015 literature
says, it is not there any more. The first-30 fade at 15:30 is +0.4 bp: D487's −0.10 slope is
real as a statistic and worthless as a trade, because the last-30 σ is small and the sign is
only usable in 2020–2022. ρ(E1, K8) is +0.32 — the turn-of-month days are partly after-down
days.

## 3. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a K8 NQ 45–50%, +9–12 bp, hit 55–58%, Sharpe 0.40–0.60, ≥ 6 of 8, both subs; ES +4–6 bp, 0.15–0.35; ρ 0.6–0.7 | | 44%; +11.6; 57%; **+0.61**; 6 of 8; both; ES +4.9, +0.18; ρ +0.70 | right (the Sharpe at the top of the range) |
| X-b TOM +8–15 bp, above N1, z 1.5–2.5, Sharpe 0.3–0.5 | | +6.9; inside N1; z +0.46; +0.22 | wrong: weaker than published |
| X-c FOMC +8–20 bp, inside or marginal | | +2.8; inside | size below the range; verdict right |
| X-d E3 +3–6 bp, N1 pooled, Sharpe 0.1–0.4 | | +0.4; inside; −0.53 | wrong |
| X-e ρ(E1,K8), ρ(E2,K8), ρ(E3,K8) < 0.3; ρ(E3, ungated) < 0.2 | | **0.32**; 0.08; −0.02; 0.02 | E1 just over |

## 4. What stands

- **The ledger has its first entry, PROVISIONAL**: K8. It goes into the assembled book's
  tests when there is a second component; on its own it is one component at ≈ 0.6 in-sample,
  which is the altitude the book is built from and not the book.
- **Promotion is the forward read**, declared in D498 §3 (FULL if the forward gross mean > 0,
  net Sharpe > 0 and the difference against after-up days has z ≥ 1; REMOVED if the net Sharpe
  < −0.3 or the difference is negative). About 680 sessions, ≈ 300 trades: at the in-sample
  size the difference would show at roughly 2 SE. **Not run; the principal's word.**
- **No second clock yet.** Turn-of-month and FOMC did not carry on this data; the first-30 fade
  is not a trade. The second component has to come from a different instrument or a different
  state, and every session-window and overnight construction on the eight roots is already
  scored.

## 5. Files

Runner · eight trade files · the artefact · this record · the ledger entry.
