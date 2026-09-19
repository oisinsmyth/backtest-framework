# D564 RESULT — **as pre-registered, DOES NOT PASS** (+0.42 gross, rank 0.80); **under a formation-rule amendment that repairs two calendar defects, PASS** (+0.69 gross / +0.99 Sortino, rank 0.972 in N1, 0.971 in N2, 0.975 in the name-randomised N3) — the first PASS of the deposit series, carried by seasonal roots and by the two years the amendment restored, and sharing carry's worst days

*2026-09-20. Spec committed in `2da64b6` BEFORE the runner (R8). Primary window 2016-01-04 →
2023-12-29 (2,065 sessions, 97 formation month-ends); long window 2011-06-30 (first eligible
formation) → 2023-12-29 as the declared diagnostic; **the 2024+ slice was not read** — this line
keeps its holdout. Nothing admitted (R15). Runner `scripts/run_d564_basis_momentum.py`, output
`data/d564_basis_momentum.json`, 99 s.*

**The order of events matters and is stated first.** The runner was built to the
pre-registration, run once, and read +0.42 at the 80th percentile of its null — inside. The
eligibility table beside it showed **24 of 97 formation month-ends flat** (fewer than 12 eligible
roots) and 2021 with no position at all. The diagnostic traced every one of them to two sessions:
**2020-06-30**, a truncated day in the raw archive (237 of ~900 settlements), and **2021-05-31**,
Memorial Day, in the session calendar because a Globex evening bar exists but with no settlements.
Each voided one or two monthly returns for every root and so twelve month-ends each. The
formation rule was amended to D556's: **the formation settlement is the last finite one within
five sessions ending at the month-end**, applied to every cell alike, with the pre-registered
number and its null kept beside. **The amendment was made after the pre-registered percentile
had been read.** The reader weights that; the record does not hide it. §2 measures exactly what
the amendment changed.

---

## 1. The declared verdicts

| | as pre-registered (month-end session alone) | **amended (last settlement within 5 sessions)** |
|---|---:|---:|
| PRIMARY — EW High4/Low4, gross Sharpe / Sortino 2016–2023 | +0.421 / +0.602 (SE 0.31) | **+0.692 / +0.990** (SE 0.31) |
| flat formation month-ends of 97 · mean eligible roots | 24 · 12.9 | **0 · 17.0** |
| N1 purged rotation (1,562 offsets): p05 · p50 · p95 · rank | −0.30 · +0.12 · +0.74 · **0.796** | −0.44 · +0.10 · **+0.537** · **0.972** |
| N2 family of four: best · p50 · p95 · rank | +0.49 (time-series) · +0.22 · +0.77 · 0.80 | **+0.692 (primary)** · +0.16 · **+0.563** · **0.971** |
| N3 name-randomised (2,000 draws): p95 (SE) · rank | +0.545 (0.014) · 0.896 | **+0.597 (0.017)** · **0.975**, margin **5.5 SE** |
| **verdict** | **DOES NOT PASS** | **PASS** |
| harness · orthogonality | OK · DISTINCT | OK · DISTINCT |

| # | prediction | value (amended) | |
|---|---|---|---|
| P-1 | primary > 0, above N1 p95; point 0.25–0.55 | +0.692, p95 +0.537 | **holds**; above the point range |
| P-2 | \|ρ(BM, basis)\| < 0.7, point −0.2 … +0.2; \|ρ(BM, mom)\| < 0.5 | **−0.24**; **+0.49** | **holds**; basis outside the point range, mom 0.01 inside its bound |
| P-3 | turnover > D557's 5.6 wu/yr; point 8–15 | **4.2** | **fails** — High4/Low4 turns over less than the tercile sort |
| P-4 | M6: 2016–2023 ≥ 2011-07 … 2015 | +0.69 ≥ +0.46 | **holds** — no post-2010 decay |
| P-5 | c5 on carry A's worst days < 0, point −0.1 … −0.4; DD ratio not below null p05 | **−0.29 σ**, rank **0.005**; 0.73 | **holds**, at the bottom of the null |
| P-6 | higher return in high-vol formation months | Sharpe **1.15 vs 0.36** (monthly, 48 / 48) | **holds** |
| P-7 | spreading return > 0 | Sharpe +0.16 | **holds** |
| P-8 | P&L positive on ≥ 9 of 17 roots, 2011–2023 | **14** | **holds** |
| P-9 | dollar σ > $500 | $3,803 | **holds** |
| P-10 | falsifiers | none fires | |

Eight of nine held under the amendment (six of nine as pre-registered: P-1, P-3, P-4, P-7 failed
there — P-4 and P-7 flip because the restored 2021–2022 months carry both).

## 2. What the amendment changed, measured

The two books were compared on the sessions **both** position (73 formation month-ends, 1,547
sessions): Sharpe **+0.49 as pre-registered against +0.52 amended, daily correlation 0.95**.
Memberships differ on 15 of the 73 (December 2018 → May 2020, where a partial-settlement day sat
inside the ranking window and moved one or two monthly returns); the T1 choice differs at 32 of
1,649 root-month-ends. **On the sessions only the amended book positions — the 24 months from
June 2020 to May 2022, 518 sessions — it earned +0.28 of the +0.64 total at a Sharpe of +1.21.**
The amendment therefore did two things: it left the common 73 months essentially where they
were, and it restored the 2021–2022 commodity run, which is where the family's best years are
(2022 **+2.71**, 2021 +0.52). Without those months the primary is +0.42 and inside the null; with
them it clears three nulls. **That is the size of the PASS's dependence on the repair.** The
repair itself is not in doubt — a Memorial Day and a truncated archive day are not signal — but
the reader should know that the passing statistic is the pre-registered construction plus its
two strongest years.

## 3. Performance — net and gross, the four groups (amended, 2016–2023)

**EW High4/Low4 (the paper's High-minus-Low at half scale):**

| | gross | net (turnover) | net incl. rolls |
|---|---:|---:|---:|
| Sharpe / Sortino | **+0.692 / +0.990** (SE 0.31) | +0.683 / +0.978 | +0.639 |
| ann. vol · total · max DD | 11.3 % · +63.9 % · **−28.5 %** | | |
| hit (days) · skew · kurtosis | 51.2 % · −0.17 · 5.1 | | |
| turnover · cost | **4.2** weight-units/yr → 9.8 bp/yr | | |
| breakeven | **184 bp/side** against ~1 modelled | | |

Eras: 2011-07 → 2015 **+0.46**, 2016–2019 +0.68, 2020–2023 **+0.72**. Years: 2016 +0.63, 2017
**+2.01**, 2018 +0.22, 2019 +0.03, **2020 −1.09**, 2021 +0.52, **2022 +2.71**, 2023 +1.27. Seven
of eight positive; 2020 is the April crude collapse with CL in the short leg on the wrong side of
the negative print.

**Group 2 — root-months (768):** mean +8.3e-4, **median +11.6e-4** (the body earns), win 55 %,
payoff 0.98, skew −0.65; ex-top-1 % +3.7e-4, ex-bottom-1 % +13.9e-4, symmetric trim **+9.3e-4**
(112 % of the mean). Top 1 % of root-months carry 56 % of P&L. **The long leg carries the book:**
long root-months mean +13.3e-4 (median +21.6e-4, win 58 %), short root-months +3.3e-4.

**Group 3 — what it depends on.** Two roots reach half the P&L: **NG +0.18 and ZL +0.15 of the
+0.64 total**; top-1 / 5 share 29 % / 88 %. NG is in the **short leg on 81 of its 83 positioned
month-ends** — a persistent short of the most seasonal, most contangoed curve in the universe.
The grains and livestock (ZL, ZC, ZM, ZW, LE, HE, ZS) contribute +0.51 between them. Energy nets
to nearly nothing (HO +0.08, CL −0.06, RB −0.11, BZ +0.02) and the metals to nothing (HG +0.03,
PL +0.02, GC, SI, PA ≈ 0 or negative). **The declared non-seasonal diagnostic — High3/Low3 on the
nine energy and metal roots — reads −0.09.** The effect on this universe lives in the seasonal
curves, which is exactly the deposit's §6.4 warning that a slope-change measure on a seasonal
curve reads the calendar. Whether that is the published effect or a seasonal-roll artefact, this
record cannot say; a de-seasonalised construction is a different, declared study.

**Group 4 — the nulls** in §1. The rotation null's median is +0.10 (tilt, as in every persistent
book here); the name-randomised null's median is 0.00 and its p95 +0.60 with a bootstrap SE of
0.017, so the observed +0.69 is **5.5 SE above it — resolved, not UNRESOLVED**. The timing of
which roots fill the legs carries information beyond the leg structure.

**The family.** EW terciles +0.545 / +0.781 (rank 0.983 in its own N1, also above its p95); dollar
High4/Low4 net +0.359 (rank 0.929, inside); the time-series form **+0.219** (rank 0.948, inside),
weaker as the deposit predicted — and as pre-registered it had read +0.49 above its own p95, the
one cell that then cleared, which the amendment took away. The family maximum is the primary.

## 4. The component line

| | dollar High4/Low4, 16 roots at minimum size | C-d-eligible sub-book (CL GC HG NG SI ZC) |
|---|---:|---:|
| **C-a** net Sharpe / Sortino | **+0.359 / +0.514** (gross +0.379) | **+0.485 / —** |
| **C-c** skew | **+0.01** | |
| **C-d** daily σ | **$3,803** — 7.6× the cap | **$340 — under the cap** |
| hit · total · max DD | 50.3 % · +$177,594 · −$183,500 | |
| cost | $9,948: 1,291 sides + 1,168 roll sides | |
| largest root | **HO +$66k (37 %)**, ZL +$36k, ZM +$21k; RB −$25k, PA −$14k | |
| N1 rank (net) | 0.929 | |

**Not entered: fails C-a (+0.36 < 0.5) and C-d.** But note the sub-book: the six roots whose
minimum-size σ fits the account read **net +0.485 at σ $340 with skew +0.01** — under the C-d
cap and 0.015 short of the C-a bar. It is a subset of a sort formed on 17 names, not a
construction of its own, and it is 6 roots with 4-and-4 legs drawn from 17; it is reported, not
promoted. ρ with the ledger's live entry remains absent.

## 5. Orthogonality and the tail

**T0 (the deposit's stop rule):** mean cross-sectional Spearman of BM with the paper's basis
**−0.24** (pooled −0.27), with `carry_ann` +0.25, with 12-month momentum **+0.49**. Distinct from
carry; close to the momentum bound, which is arithmetic — BM's first term *is* the 12-month
momentum of the nearby.

**T4 (the deposit's own worst-case):** on D556 carry A's worst 5 % of days basis-momentum loses
**0.29 σ**, positive on 40 % of them, at the **0.5th percentile** of its rotation null (whose
median is 0.00); the vol-matched blend's drawdown ratio is 0.73 against a null median of 0.56,
i.e. it shortens carry's drawdown *less* than a random book would. Daily ρ 0.19. **The deposit
predicted this — "both are intermediary/liquidity-risk premia; check drawdown overlap, not
correlation" — and it holds: basis-momentum is carry's tail as trend was (D561).** For a book
that already holds nothing carry-like this is moot; for the deposit's programme it is the
diversification claim failing again.

**Volatility (§2.8):** the high-vol half of formation months earns a monthly Sharpe of **1.15**
against **0.36** for the low-vol half — the paper's "increasing in volatility", strongly.

## 6. What this record says, and what it does not

- **As pre-registered, the construction does not pass.** Under an amendment that repairs a
  data-calendar defect it passes three nulls with margin, on a statistic above the deposit's
  own discounted expectation, with eight of nine mechanism predictions holding. The amendment
  restored the two best years. Both numbers stand in the artifact.
- **The effect on this universe is a seasonal-curve effect.** Non-seasonal roots read −0.09;
  NG is short 81 of 83 months. That is not the paper's claim (the paper finds it in FX and equity
  indices too) and it is the first thing a follow-up should separate: a de-seasonalised BM, or
  the 21-commodity universe, pre-registered.
- **It is not a hedge for anything carry-like**, and it shares carry's worst days at the bottom
  of its null.
- **No vehicle at full size**; a six-root sub-book sits just under the C-a bar at a σ the account
  can carry — worth its own pre-registration as a construction, not as a subset.
- **The holdout is intact.** This is the first line in the deposit series whose 2024+ slice is
  unread and whose in-sample result would justify reading it. That read is the principal's call
  and it is the only thing that can turn "PASS under amendment" into a confirmation.
- Not done: no ranking-period variant, no de-seasonalisation, no FX/equity extension, no
  Internet Appendix replication (paywalled; the construction was taken from Kwon–Kang–Yun's
  closed form), no COT negative control. The three audits, the BM second path (300 cells, exact
  to 1e-10), the held-contract audit (100 %), the leg-membership audit and the exactness guard
  each ran and each was proven to raise; all in the json.
