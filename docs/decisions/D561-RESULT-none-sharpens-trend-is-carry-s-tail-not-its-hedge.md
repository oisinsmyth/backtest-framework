# D561 RESULT — **none of the three sharpens it at the declared standard**: the 13-year null is as wide as the 8-year one and its centre moves up (S1); a leverage cap costs Sharpe monotonically and buys 0.8 points on a worst day that is a macro day, not a levered one (S2); beside equities trend sits at the 94th percentile of a random sign book on the worst days and the bar was 95 — and beside carry it is **the opposite of a hedge**: −0.56 σ on carry's worst days, below every one of 1,562 rotations (S3)

*2026-09-19. Spec committed in `72f0c58` BEFORE the runner (R8). Primary window 2016-01-04 →
2023-12-29 (2,065 sessions) for S2 and S3; S1 on 2011-01-03 → 2023-12-29 (3,353 sessions) by
declaration; **the 2024+ slice was not read.** Nothing admitted (R15). Nothing closed. Runner
`scripts/run_d561_trend_sharpenings.py`, output `data/d561_trend_sharpenings.json`, 38 s. The
rebuilt D555 primary and D556 cell A reproduced their artifacts to 1e-9 before anything was scored.*

**Six of thirteen predictions held, and the declared falsifier of S3 fired.** The ones that held
are about direction (the cap lowers Sharpe, the worst day shrinks, trend is uncorrelated with
equities, the carry blend's drawdown is diversification); the ones that failed are the ones that
put a magnitude on a null. Twice the miss was 0.02: c5 on equities +0.255 σ against a p95 of
+0.276, and the equity blend's drawdown ratio 0.489 against a p05 of 0.463. Both nulls are exact
(enumerated, SE 0), so those are misses, and the record says how thin they are rather than moving
the bar. The one result nobody predicted is the carry pair, and it is the finding.

---

## 1. The declared verdicts

| | statistic | observed | null | verdict |
|---|---|---:|---|---|
| **S1 power** | 12m book, gross Sharpe **2011–2023** | **+0.462** (SE 0.29); Sortino +0.657 | N1-L purged, 2,850 offsets: p05 −0.64, **p50 +0.11**, p95 **+0.89**, sd 0.51; rank **0.677** | **INSIDE** |
| **S2 sizing** | CAP = 10 book, gross Sharpe 2016–2023 | **+0.250** (SE 0.35); Sortino +0.351 | N1: p50 −0.07, p95 +0.87, rank 0.771; N2 (4 caps): best +0.272 (cap 20), p50 −0.04, p95 +0.91 | **DOES NOT PASS** |
| **S3 role** | c5: trend's mean return on ES's worst 5 % of days, in trend σ | **+0.255** (hit 53 %) | N1-O: p05 −1.05, **p50 −0.68**, **p95 +0.276**; rank **0.939** | **NOT DISTINGUISHED** at p95 |

| # | prediction | value | |
|---|---|---|---|
| S1-P1 | sd(N1-L) 0.38–0.48 | **0.512** (8-year null 0.583; ratio 0.88 against √(2065/3353) = 0.78) | **fails** |
| S1-P2 | p95 0.60–0.80; rank 0.80–0.95 | p95 +0.887; rank 0.677 | **fails** |
| S1-P3 | falsifier: clears p95 | no | does not fire |
| S2-P1 | cap 10 < +0.304; point 0.10–0.30 | +0.250 | **holds** |
| S2-P2 | worst day smaller; kurtosis falls | −6.03 % vs −6.83 %; 4.9 vs 5.4 | **holds** |
| S2-P3 | top-3 root share < 50 % | 53 % (uncapped 60 %) | **fails** |
| S2-P4 | Sharpe monotone in CAP | +0.07 / +0.20 / +0.25 / +0.27 / +0.30 | **holds** |
| S2-P5 | nothing clears N1 or N2 | nothing does | **holds** |
| S2-P6 | falsifier: cap 10 > +0.304 | no | does not fire |
| S3-P1 | c5 on ES > 0, above p95; point 0.15–0.50 | +0.255, p95 +0.276 | **fails by 0.02 σ**; inside the point range |
| S3-P2 | c5 on carry > 0; point 0.10–0.40 | **−0.556** | **fails**, and not narrowly |
| S3-P3 | ES blend DD ratio below null p05 | 0.489, p05 0.463 | **fails by 0.026** |
| S3-P4 | carry blend DD ratio < 1, not below p05 | 0.462, p05 0.309 | **holds** |
| S3-P5 | ρ(trend, ES) daily in [−0.30, +0.10] | −0.127 | **holds** |
| S3-P6 | falsifier: S3-P1 and S3-P3 both fail → diversification, not convexity | | **fires** |

## 2. S1 — the null does not narrow with the window, and its centre moves

The prediction assumed a rotation null of a monthly-hold book scales like independent draws in
the number of sessions. It does not. From 8 to 13 years (+62 % sessions) the null's sd fell from
0.583 to **0.512** (−12 %), and its median moved from −0.07 to **+0.11**: a randomly-timed
persistent sign book on these 36 roots *earns* over 2011–2023, because the average sign is long
bonds and long equities and both rallied. The observed +0.46 is then +0.35 above its null's
median — the same excess the 8-year book has (+0.30 above −0.07) — inside a null that is nearly as
wide. Sortino: observed +0.66 against p50 +0.16 and p95 +1.34. The unpurged long-window null has
its maximum +2.47 at offset 3,255, 98 sessions from the cycle end: the look-ahead signature D555 §2
documented, again.

**The lever is dead.** A longer window of the same fixture does not buy the test power, because
the null's width is set by the number of regimes the persistent book can be rotated across, not by
the session count, and the extra years bring their own tilt. The programme's standard on this
construction cannot be met by waiting for more data of this kind.

## 3. S2 — the cap prices the rates leverage, and it was not where the tail lived

| cap | binds on (root-months, of 96 month-ends) | gross Sharpe / Sortino | net | max DD | worst day (2021-11-26) | top-3 share | FI Sharpe |
|---|---|---:|---:|---:|---:|---:|---:|
| **∞ (D555)** | — | **+0.304 / +0.426** | +0.293 | −36.4 % | **−6.83 %** (ZT) | 60 % | +0.44 |
| 20 | ZT 78, SR3 11, ZF 6 (2.9 %) | +0.272 / +0.381 | +0.261 | −35.8 % | −6.34 % (HO) | 54 % | +0.38 |
| **10** (declared) | ZT 95, ZF 73, ZN 38, SR3 14 (6.8 %) | **+0.250 / +0.351** | +0.240 | −35.1 % | **−6.03 %** (HO) | 53 % | +0.35 |
| 5 | + ZN 87, TN 59, all six FX, ZB 29 … (21.8 %) | +0.199 / +0.279 | +0.189 | −33.6 % | −5.38 % (HO) | 64 % | +0.30 |
| 1 (equal notional) | 90 % of positioned root-months | +0.068 / +0.095 | +0.059 | −20.8 % | −2.44 % (BTC) | 197 % | +0.27 |

Every cap lowers the Sharpe (S2-P4 holds exactly), and the declared cap costs 0.05 for 0.8 points
on the worst day and 1.3 points of drawdown. **The worst day is the same session at every cap:
2021-11-26, the Omicron Friday**, when crude fell 13 % and the curve rallied together. D555 §3 read
that day as the levered two-year note's; with ZT capped the largest loser is heating oil and the
day is 6.0 % instead of 6.8 %. The tail was a cross-asset day, not a leverage day. The best day is
also the same at every cap (2020-03-09, +7.1 % uncapped). Turnover falls from 14.7 to 10.4
weight-units a year at cap 10 and breakeven rises from 30 to 33 bp/side; cost was never the
constraint. Sectors at cap 10: FI +0.35 (from +0.44), EQ +0.34, FX +0.12, CM −0.06, unchanged
outside FI because the cap binds nowhere else. Roots to half the P&L: 3 at every cap above 1. Per
year the ordering is D555's at every cap (2016 −1.8, 2020 +1.7, 2022 +1.5, 2023 −0.6).

**The component line is D555 §4's**, re-emitted from the same signs and asserted equal: net
**+0.060**, gross +0.082, skew −0.61, σ **$8,762** a day, $24,786 of cost over 3,780 sides. A cap on
return-space weights does not alter a one-contract-per-root book. **Not entered; fails C-a, C-c,
C-d.** ρ with the ledger's live entry remains absent.

## 4. S3 — the overlay, against a null that diversifies as well as noise

Bases 2016–2023: ES long-only Sharpe +0.67 (Sortino +0.94, vol 18 %, max DD −38.5 %); 60/40
+0.65 (+0.93); D556 carry A −0.20 (−0.28). Overlay: the 12m book +0.30 (+0.43); the cap-10 book
+0.25 (+0.35), diagnostic, and it moves nothing below by more than 0.02.

| pair | ρ daily / monthly | **c5** (hit) | c5 null p50 / p95 / rank | c10 (rank) | **DD ratio** | DD null p05 / p50 / rank | Sharpe base → blend |
|---|---:|---:|---|---:|---:|---|---:|
| **trend \| ES** | −0.13 / −0.30 | **+0.255** (53 %) | −0.68 / **+0.276** / **0.939** | +0.05 (0.88) | **0.489** | **0.463** / 1.05 / 0.088 | +0.67 → **+0.74** |
| trend \| 60/40 | −0.16 / −0.31 | **+0.424** (61 %) | −0.61 / +0.360 / **0.976** | +0.15 (0.93) | 0.481 | 0.459 / 1.05 / 0.078 | +0.65 → +0.74 |
| **trend \| carry A** | +0.18 / +0.14 | **−0.556** (32 %) | −0.14 / +0.433 / **0.000** | **−0.54** (0.000) | 0.462 | 0.309 / 0.76 / 0.191 | −0.20 → +0.07 |

**Beside equities.** Trend earned in four of ES's five worst months (March 2020 **+19.9 %**,
September 2022 +7.8 %, April 2022 +5.8 %, June 2022 +4.7 %; December 2018 −6.0 %), its 103 worst
ES days are 32 in 2020 and 30 in 2022, the vol-matched blend halves the equity drawdown (−33.7 σ
→ −16.5 σ) and lifts the Sharpe from +0.67 to +0.74. That is what the literature says, and the
null says how much of it a random persistent book on the same 36 roots also does. **The median
random book loses 0.68 σ on ES's worst days** — it is long-tilted, as a book of momentum signs on
a decade of rallies is — and trend's +0.255 is 0.93 σ better than that median and at the 94th
percentile. The declared bar was the 95th, and 5 % of the 1,562 rotations do as well or better on
those days, because a rotation that happens to place 2022's short-bond signs or 2020's short
signs under the crash months is a random book that hedges. On the 60/40 base c5 clears its p95
(0.42 against 0.36, rank 0.976): 2022 is 37 of that base's 103 worst days and trend was short
bonds through it. The 60/40 pair was declared diagnostic and stays diagnostic; the declared
statistic is on ES and it missed by 0.02 σ. On the drawdown, the blend's ratio 0.489 sits at the
9th percentile of the null (whose median, 1.05, *lengthens* ES's drawdown, being long-tilted) and
above the 5th by 0.026.

**Beside carry, the result is not thin and it is not what the deposit says.** On carry's worst 5 %
of days trend loses **0.56 σ**, positive on 32 % of them, and **every one of the 1,562 rotations
does better** (null p50 −0.14, p95 +0.43). The same on the worst 10 % (−0.54, rank 0.000). The
daily correlation is +0.18, exactly D556's number and inside the deposit's "roughly 0 to 0.2" —
and it is the body of the distribution. In the tail the two books are the same book: carry's worst
days are sharp reversals of the prevailing curve state on the roots where the prevailing trend is
on the same side (backwardation with an uptrend in commodities, positive carry with a long bond
position through 2022), and D556 §5 already recorded that on the rates legs carry's sign is close
to a constant. The blend's drawdown ratio 0.462 is below the null's median 0.76 (rank 0.19), so
trend does shorten carry's long 2016–2020 decline more than the median random book does — that is
the drawdown D556 §4 measured, and it is diversification against a slow loss, as S3-P4 predicted.
What D556 §4 could not see, because it read a correlation and a drawdown, is that **the days carry
loses most are days trend loses too.** The deposit's reason for holding both — "uncorrelated, so
the worst stretch is shallower" — is true of the stretch and false of the days.

## 5. What the three evaluations say together

The assessment that prompted this record was that the signal could not be sharpened and the three
real levers were power, sizing and role. Evaluated:

- **Power does not accrue.** The rotation null of a persistent sign book is ~0.5 wide on 8 years
  and on 13, and its centre drifts with the window's tilt. There is no window of this fixture on
  which a +0.3-to-+0.5 trend book clears the programme's standard.
- **Sizing prices a risk that was not the tail.** The cap trades Sharpe for breadth monotonically
  and the worst day is a macro day at every cap. A covariance-scaled (HOP) book is a different
  construction and this record predicts, from S2-P4, that it would sit below D555's Sharpe too.
- **Role is directionally what the literature says beside equities and not what the deposit says
  beside carry.** Trend beside equities is at the 94th percentile on the worst days and the 9th on
  drawdown, against a bar of 95 and 5; the honest reading is that on this window its convexity is
  not separable from the luck of a random persistent book at the declared confidence, and that
  sits with D555's own finding that the effect here is two events. Trend beside carry is a
  tail-concentrator, not a hedge, and that is the finding this record adds: **ρ measures the body;
  score the overlay on the base's worst days against a rotation null before calling two components
  diversifying.** The ledger's C-b (ρ < 0.3) is a body statistic, and this record recommends the
  worst-day c5 with its null beside it for any pair entered.

## 6. What was not done, and what is still wrong with this

- **The 60/40 base clears where ES does not**, and that is a fact about which base the 2022 bond
  selloff sits in, not a licence to prefer the base that passes. Recorded, not promoted.
- **The bases are not the prop book.** The ledger's live arm has no daily P&L on disk; the
  overlay on it is the question that matters for `BOOK_PROP.md` and it is unanswered.
- **A name-randomised null** (rotate which root carries which sign, keep the count) would separate
  the long-tilt of the rotation null from its timing; the rotation null's median of −0.68 σ on ES's
  worst days is that tilt, and the c5 margin of 0.02 σ is measured against a null that carries it.
  Not run; it is the same read as PICKUP's standing item for the sorts.
- No de-seasonalised carry in B3, no HOP-style covariance scaling, no reversal leg. The 2024+
  slice remains unread for every construction here.
- The three audits ran and each was proven to raise; the cap audit, the worst-day audit and the
  two artifact reproductions are in the json `audits` and `harness` blocks.
