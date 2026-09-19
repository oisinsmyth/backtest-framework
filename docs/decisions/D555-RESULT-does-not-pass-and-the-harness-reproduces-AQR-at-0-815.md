# D555 RESULT — **DOES NOT PASS**, and the harness reproduces AQR's own series at ρ = 0.815: on 2016–2023 the published 12-month trend book scores +0.30 gross inside a null whose p95 is +0.95, and AQR's updated factor reads −0.02 on the same window

*2026-09-19. Spec committed in `5ed655b` BEFORE the runner (R8). Primary window 2016-01-04 → 2023-12-29
(2,065 sessions); long window 2011-01-03 → 2023-12-29 (3,353 sessions) as the declared diagnostic;
**the 2024+ slice was not read.** Nothing admitted (R15). Nothing closed. Runner
`scripts/run_d555_tsmom_replication.py`, output `data/d555_tsmom_replication.json`, 112 s.*

**The harness half of the record passes cleanly and the strategy half does not.** The 36-root
replication of Moskowitz–Ooi–Pedersen's construction correlates 0.815 monthly with AQR's *Time
Series Momentum: Factors, Monthly* over 156 months (commodities 0.82, fixed income 0.85, FX 0.66,
equities 0.55), and its 2011–2023 Sharpe (0.44 monthly) is *above* AQR's (0.30). The data layer and
the construction are right. **What the published effect delivered on 2016–2023 is what it
delivered:** +0.30 here, **−0.02 on AQR's own updated factor**, and neither number distinguishes
itself from a randomly-timed persistent sign book.

---

## 1. The declared verdict

| | | |
|---|---|---|
| **PRIMARY** — 12m published book, gross Sharpe 2016–2023 | **+0.304** (SE 0.36) | N1 purged: p50 −0.07, **p95 +0.95**, rank 0.78 → **INSIDE** |
| **N2 family**, 10 declared cells | best **+0.340** (3+12 / published) | p50 **+0.34**, p95 +1.06, rank 0.50 → **INSIDE** — the family's best is the null's median |

| prediction | | |
|---|---|---|
| **P-1** primary > 0, above N1 p95; point 0.4–0.8 | +0.304, p95 +0.946 | **fails** (positive, below the point range, inside the null) |
| **P-2** harness: ρ with AQR ≥ 0.5, point ≈ 0.7 | **+0.815** | **holds**, above the point |
| **P-3** 12m > 3m > 1m, and 1m < 0.3 | 0.30 / 0.22 / 0.24 | **fails** on the ordering (1m above 3m); 1m < 0.3 holds |
| **P-4** 12m P&L positive on ≥ 21 roots, 2011–2023 | **26 of 36** (24 of the 32 full-span) | **holds**; 22 of 36 on 2016–2023 |
| **P-5** dollar book net 0.3–0.7, gross − net < 0.1, full book fails C-d | net **+0.06**, gross +0.08, σ **$8,762**/day | **fails** on the Sharpe range; the cost and C-d clauses held |
| **P-6** 2016–2019 weakest (< 0.3), 2020–2023 strongest | **−0.20** / +0.74 / (2011–2015 **+0.82**) | **fails** — 2016–2019 is weakest, but the strongest era is 2011–2015 |
| **P-7** falsifier branches | primary above p50; P-2 holds | **neither branch fires**: the harness is fine and trend did modestly here |

Two predictions of seven held. The two that did are the ones that test the *instrument* (P-2) and
the *breadth* of a documented effect (P-4); the four that failed are the ones that inherited a
magnitude from the literature.

## 2. The null was amended on the first run, and the record says how

**As pre-registered, N1 enumerated every offset 1 … L−1 and was contaminated.** An offset k puts
the sign from session t+k (mod L) at session t. For k within one lookback of L that is a sign
computed **up to 252 sessions in the future**, whose 12-month window *contains* the returns being
scored: the un-purged null's best offset was L−95 at Sharpe **+2.70**, and at that offset every one
of the 36 roots earned at once (per-root Sharpe ≈ +1 each) — look-ahead's signature, not trend's.
For k within a lookback of 0 the sign is a *staler* momentum read, which is still momentum. The
memory rule this violates is the one written after D494: *a control must not overlap the outcome.*

**Amendment, made before any percentile was read as a verdict and applied to all ten cells alike:
offsets within 252 sessions of either end are purged** (1,562 of 2,064 remain). The un-purged
figures are kept beside the purged ones in the json (`per_cell_unpurged`), and the full profile of
null Sharpe against offset is stored for the primary. That profile is a finding in itself:

| shift of the sign (sessions) | −252 … −21 | −21 … −1 | +1 … +21 | +63 … +126 | **+252 … +504** | +504 … +1,561 |
|---|---:|---:|---:|---:|---:|---:|
| mean null Sharpe | **+2.3** | +1.3 | +0.15 | +0.46 | **−0.76** | +0.04 |

A sign lagged three to six months still earns (+0.46, momentum's persistence); **a sign lagged one
to two years earns −0.76** — the long-horizon reversal the literature documents beside momentum.
The rotation null of a slow signal therefore carries the return autocorrelation at every lag, and
the observed sits at the 78th, 72nd or 51st percentile depending on whether the purge is 252, 504
or 756 sessions. **No choice of band takes the primary out of its null**, and the purge is the one
declared here, not the best of those three.

## 3. Performance — net and gross, the four groups

**Published book (return space, MOP's equal average of 40%-vol positions), 2016–2023:**

| | gross | net (turnover) | net incl. rolls |
|---|---:|---:|---:|
| Sharpe | **+0.304** (SE 0.36) | +0.293 | +0.255 |
| ann. vol | 14.6% | | |
| total return | +36.4% over 8 years | | |
| max drawdown | **−36.4%** | | |
| hit (days) | 52.0% · skew −0.20 · kurtosis 5.4 | | |
| turnover | 14.7 weight-units a year → **15.6 bp a year** at the modelled ~1 bp/side | | |
| **breakeven cost** | **30.1 bp/side** against ~1 bp/side modelled — cost is not the constraint | | |

Long window 2011–2023: gross **+0.46**; AQR's factor over the same months +0.30.

**Group 2 — the distribution of root-months (3,249 root-months, 2016–2023, in units of book return):**
mean +1.12e-4, **median +2.7e-5** (the mean is four times its median: the tail is doing the work),
win 50.4%, payoff 1.07, skew +0.43, kurtosis 3.2. **Ex-top-1% the mean is −1.3e-5; ex-bottom-1%
+2.18e-4; the symmetric trim gives +0.93e-4** (83% of the mean). The top 1% of root-months carry
**111% of the P&L**, and on the symmetric trim the body is still positive — a two-sided fat-tailed
book, not a lottery book, and a thin one. Long months are 47% of the sample and earn +2.8e-4 a
month; short months earn −0.4e-4.

**Group 3 — what the winners depend on.** Three roots reach half the P&L: **ZT, ZF, NQ**. Top-1 /
top-5 / top-10 root share of the total: **28% / 84% / 127%** (the bottom 26 roots net to a loss).
Sectors 2016–2023: fixed income **+0.44**, equities +0.34, FX +0.12, **commodities −0.06**. Per year:
2016 **−1.67**, 2017 +0.95, 2018 −0.17, 2019 +0.18, 2020 **+1.74**, 2021 −0.20, 2022 **+1.66**,
2023 −0.61 — **four of eight years positive**, and the two big years are the two crisis-trend years.
Per root the best five are ZT +0.97, ZF +0.62, NQ +0.51, ZL +0.48, TN +0.41; the worst five SI
−0.55, GC −0.45, ZM −0.45, 6C −0.39, RTY −0.29.

**The ZT number carries a construction fact.** MOP's 40% vol target on a two-year note future whose
ex-ante vol fell to **0.3%** is a position of **121× notional**; SR3 reached 111×, ZF 26×. The
published construction has no cap and this record applies none, so the rates legs of the book are
levered exactly as the paper's are — which is also where the book's largest single days come from
(ZT −6.8% on 2021-11-26, SR3 −4.5% on 2023-03-13).

**Group 4 — the nulls** are in §1 and §2: p50 −0.07 and p95 +0.95 for the primary, SE 0 by
enumeration, and the null is **decisive** in the sense that nothing here approaches its p95.

## 4. The component line — dollar book at minimum size

One minimum-size contract per root per sign, 34 roots (BZ and SR3 excluded on roll count, as
declared), monthly holds, **$3 a round trip on a micro / $6 on a full contract plus one tick
crossed, a roll charged as two sides**, 2016–2023:

| | 12m dollar book | C-d-eligible sub-book (17 roots) |
|---|---:|---:|
| **C-a** net Sharpe | **+0.060** (SE 0.30); gross +0.082 | +0.238; gross +0.267 |
| **C-c** skew | **−0.61** | — |
| **C-d** daily σ | **$8,762** — 17.5× the $500 cap | **$1,712** — 3.4× the cap |
| hit / total / max DD | 51.2% / +$93,534 / −$274,760 | |
| cost | $24,786 over 8 years: 3,780 sides, **3,428 of them rolls** | |
| ρ with the ledger's live entry | **ABSENT** — the MACD arm's per-session P&L is not on disk; by clock (monthly holds against a day-session arm) it is expected near zero, and that is an expectation, not a number | |

Root-month gross at minimum size: n 3,139, mean **$29.8**, median $15.0, trimmed $19.6, win 51%,
kurtosis 31. The largest dollar contributors are the full-size rates contracts (UB +$35k, TN +$34k,
ZN +$23k) because a full contract is the minimum size there; the largest losers are RB −$33k, ZM
−$27k, PL −$27k. **Not entered. Fails C-a, C-c and C-d; C-e provenance is this record.** The 1-month
dollar cell reads +0.27 net and is the family's best dollar cell at the 80th percentile of its null;
it is not promotable and the pre-registration said so.

## 5. What this says against the deposit's document

`PUBLISHED_STRATEGIES.md` §2 predicted "expected net Sharpe 0.45–0.65" for a 12m (+3m) micro book
and offered the rule "expect half the published Sharpe". On this fixture and window the answer is
**+0.29 net for the published construction and +0.06 for the one that can be traded at minimum
size** — a quarter of the published 1.13, not half, and AQR's own factor did worse. The document's
sharper claims fared better than its magnitudes: the 1-month signal is indeed weak (+0.24 gross,
+0.20 net, breakeven 6 bp/side), 2016–2019 is indeed the dead stretch, and trend's P&L is indeed
carried by the crisis years. **Its calibration argument — "if the harness cannot reproduce trend,
it cannot be trusted on anything else" — is now discharged in the direction that matters: the
harness reproduces AQR.**

## 6. What was not done, and what is still wrong with this

- **No vol cap, no daily re-scaling, no cross-root covariance** — MOP as written, not HOP. A capped
  or covariance-scaled book would move the rates legs materially; that is a different construction
  and a new pre-registration.
- **Carry (the deposit's strategy 2) is untested.** The second-nearby series it needs does not exist
  as a fixture; the raw `definition` and `ohlcv-1m` archives can build it.
- **The AQR comparison is a correlation, not a reconciliation.** 0.815 with 36 roots against ~58 and
  a different vol estimator is strong; the 0.55 on equities is the weakest sector and is where
  AQR's universe (many non-US indices) least resembles this one (ES NQ YM RTY NKD).
- **The null's width is a property of the window, and it is the finding.** With persistent monthly
  holds and 8 years, a randomly-timed sign book has a Sharpe sd of 0.5–0.6; the effect's own
  published post-2010 magnitude (0.73) sits below that null's p95. **This window cannot pass a trend
  book of the published size at the programme's standard.** The long window (13 years, +0.46) was not
  nulled because the pre-registration put the null on the primary; a 2011–2023 null is the obvious
  next read and costs two minutes.
- The three audits ran and each was proven to raise (json `audits`); the first run of this script
  chained returns across the fixture's Sunday placeholder rows and lost 18% of them, which the
  runner now refuses (`rows_dropped`: 22,531 placeholders, 69 one-bar weekend stubs).


---

*Addendum, 2026-09-19, under [R17](../RULES.md#r17) (every reported Sharpe carries a Sortino).* The runner was re-run with the Sortino beside every Sharpe; no previously written number changed. **Primary 12m published book, 2016–2023: Sharpe +0.304, Sortino +0.426**; purged rotation null Sortino p50 −0.09, p95 +1.42 (Sharpe p50 −0.07, p95 +0.95). The Sortino sits above the Sharpe, as a book whose large days are the 2020 and 2022 trend years would suggest; the verdict is unchanged and every cell carries both ratios in `data/d555_tsmom_replication.json`.
