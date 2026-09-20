# D574 RESULT — **INSIDE**: basis-momentum's forward slice reads **+0.48 gross / +0.69 Sortino** on 2024-01-02 → 2026-09-09 (696 sessions, 33 months), 70 % of the in-sample figure and inside both forward nulls (rank 0.73 in the full-span rotation, 0.80 in the name randomisation, whose 95th percentiles on a 33-month window sit near +1.0); **the composition inverted** — the seasonal roots that made the in-sample result lost (−0.47), natural gas was never in the short leg it had held 81 of 83 months, and the nine non-seasonal roots that read −0.09 in sample made +0.84; **heating oil is 86 % of the forward P&L** and March 2026 alone is 13 %; the amendment changed nothing forward; **nothing enters, and the slice is spent**

*2026-09-20. Spec committed in `7085aac` BEFORE the runner (R8), on the principal's word ("pre-
register the basis-momentum forward read and run it"). The runner refuses without
`--principals-word` and ran under it. Harness before any forward number: the in-sample primary
rebuilt on the full calendar equals D564's artifact, **+0.692157 amended and +0.420717 as
pre-registered, to 1e-9**, and D556's cell A reproduces. Six audits on the full-span objects,
each proven to raise; held-contract share 100 %. Runner `scripts/run_d574_basis_momentum_forward.py`,
output `data/d574_basis_momentum_forward.json`, 101 s (N1-full 4,048 offsets × 4 cells in 33 s,
N3 2,000 draws in 13 s). **The 2024+ slice is now spent for basis-momentum in every form on the
17 commodity roots and for the C-d sub-book.***

**Five of six numbered predictions held, and the one that failed is the one that says what
transferred.** The total is positive and inside its declared point range; the amendment is
inert forward, as predicted; two roots reach half the profit (one does); the dollar book fails
C-d with heating oil the largest line and the sub-book sits at σ $253; the book still loses on
carry's worst days. But the prediction about *who* would carry it — the seasonal roots, with
natural gas short at three month-ends in four — failed in every clause. **A transferred total
with an inverted composition is not a transfer of the in-sample result; it is a different book
under the same rule, and the record says so.**

---

## 1. The declared verdicts

| | forward observed | N1-full (3,546 offsets after purge, exact) | N3-forward (2,000 draws) | |
|---|---:|---|---|---|
| **PRIMARY** — EW High4/Low4 amended, gross Sharpe / Sortino | **+0.482 / +0.687** (SE 0.58) | p05 −0.91, p50 +0.00, **p95 +1.05**; rank **0.728** | p50 +0.01, **p95 +0.93** (SE 0.020); rank **0.798** | **INSIDE** |
| as pre-registered (ffill 1) | **+0.482 / +0.687**, identical | | | the amendment is inert forward |
| EW terciles | +0.571 / +0.787 | rank 0.755 | | |
| time-series | **+1.093 / +1.625** (in sample +0.22) | rank 0.939 | | N2's best cell |
| dollar, 16 contracts, net | **+0.989 / +1.541** (in sample +0.36) | p95 +0.89; rank **0.970** | | clears its own null on heating oil |
| N2, family of four | best +1.093 (time-series) | p50 +0.31, p95 +1.29; rank 0.870 | | inside |
| **forward verdict** | | | | **INSIDE** — no promotion; nothing enters |

| # | prediction | value | |
|---|---|---|---|
| P-1 | forward gross > 0; point 0.2–0.7 | **+0.48** | **holds** |
| P-2 | amended and as-pre-registered: 0 flat month-ends each, within 0.05 | 0 and 0; identical to every digit | **holds** |
| P-3 | seasonal contribution > non-seasonal; non-seasonal standalone ≤ +0.2; NG short ≥ 75 % | seasonal **−9.4 % (Sh −0.47)** vs non-seasonal **+27.1 % (Sh +0.84)**; standalone **+0.31**; NG short **0 %** (long 59 %) | **fails, every clause** |
| P-4 | two roots reach half a positive total | **one** (HO); top-2 share 1.28 | holds on its letter |
| P-5 | dollar fails C-d with HO or NG the largest line; sub-book σ ≤ $500 within 0.5 of +0.48 | σ $5,791, **HO +$154k**; sub-book σ $253, net **+0.04** | **holds** |
| P-6 | c5 on carry A's worst 5 % forward days < 0 | **−0.22 σ** (ρ +0.21; carry A forward −0.56) | **holds** |
| P-7 | falsifiers | inside both nulls → INSIDE; the amendment did not matter; NG not the largest loss (ZL is) | the second fires |

## 2. Performance forward — net and gross, the four groups

**EW High4/Low4, 2024-01-02 → 2026-09-09:**

| | gross | net |
|---|---:|---:|
| Sharpe / Sortino | **+0.482 / +0.687** | +0.474 / — |
| ann. vol · total · max DD | 13.3 % · +17.6 % · −11.1 % | |
| cost · hit · skew | 11 bp a year · 0.49 · −0.39 | |
| in sample, same construction | +0.692 / +0.990 | |

**Group 2 — the 33 positioned months:** mean +0.53 %, median +0.34 %, hit **0.55**, worst −6.05 %
(February 2026), best **+13.22 % (March 2026)**. By year: 2024 +0.43 (+3.6 %), **2025 −0.35
(−3.7 %)**, 2026 to September **+1.21 (+17.8 %)**. Eight of the 33 months are the eight months
of 2026 and they are the result: without March 2026 the forward total is +4.4 % over 32
months. The worst day (2026-04-08, −5.2 %) and the best (2026-04-02, +3.2 %) are three sessions
apart in the spring-2026 energy move, Brent and crude the names on each.

**Group 3 — who it was.** Root contributions in book units: **HO +15.2 %**, BZ +7.4, LE +6.1, RB
+3.7, PL +3.6, ZC +3.1, ZW +3.1, ZS +2.2, HE +0.7, GC and SI 0, PA 0, HG −0.7, CL −2.1, ZM −6.1,
**NG −8.4, ZL −10.1**. One root to half the P&L; heating oil is **86 %** of the total. In sample
the two roots to half were NG (short 81 of 83 months, +18 %) and ZL (+15 %): forward, ZL is the
largest loser and NG the second, and NG was **long** at 59 % of forward month-ends and short at
none. The seasonal eight contributed **−9.4 % at Sharpe −0.47**; the non-seasonal nine **+27.1 %
at +0.84**, and standalone as their own High3/Low3 book **+0.31** against −0.09 in sample.

**Group 4 — the nulls.** A 33-month window is wide: the full-span rotation's 95th percentile is
+1.05 and the name randomisation's +0.93, so a forward +0.48 sits at the 73rd and 80th
percentiles and neither null can decide. The dollar book clears its own rotation null (rank
0.970) because one heating-oil contract earned +$154k of +$251k, and the time-series cell — a
diagnostic, +0.22 in sample — is +1.09 forward, the family's best. Neither is the primary and
neither was predicted.

**The dollar books.** Sixteen contracts at minimum size: net **+0.99 / +1.54**, +$251,187 after
$4,027 of cost, σ **$5,791** a day, max DD −$94,522; by root HO +$154k, RB +$39k, LE +$37k, PL
+$25k, PA +$18k … ZM −$16k, ZL −$26k. The C-d sub-book (CL GC HG NG SI ZC): net **+0.04**, +$428,
σ $253, GC and SI never positioned, ZC +$5.7k against NG −$3.0k and CL −$1.6k.

## 3. What transferred and what did not

The rule transferred a positive number and nothing else. In sample the book was a
natural-gas short with soybean-oil and heating-oil longs, carried by the seasonal roots, and
its passing rank came with those names. Forward it was a heating-oil long in a spring-2026
energy squeeze, with the seasonal roots as a drag and natural gas on the other side of its own
in-sample tilt. The as-pre-registered and amended books are identical forward (no calendar
defect in the window), so the amendment's contribution was exactly the two days it repaired and
nothing about the construction. The overlay claim held: the book still loses on carry's worst
days (c5 −0.22 σ), so it remains carry's tail and not its hedge, forward as in sample.

**Why this is INSIDE and not a pass.** The pre-registration's own rule: TRANSFERS needed the
primary above both forward nulls; it is inside both. And the composition prediction failed,
which the record ranks above the total: a construction whose forward return is 86 % one root
in one season, with its in-sample carriers reversed, has not demonstrated the mechanism it
passed on.

## 4. What this settles, and what it does not

- **Settled:** the slice is spent; basis-momentum as published cannot be pre-registered on
  these roots again with any clean test. The amendment is inert beyond 2020–21. The seasonal
  tilt was the in-sample result and did not repeat. The sub-book is flat forward (+0.04) and
  its in-sample +0.48 stands as a seen number with nothing left to test it.
- **Not settled, and not claimable:** whether the rule has a positive expectation. +0.48 on 33
  months, inside nulls whose p95 is +1.0, is consistent with a modest premium and with none.
- **Nothing enters the ledger**, as the pre-registration said before the number existed: the
  16-contract book failed C-a and C-d in sample, and its forward +0.99 is one contract of
  heating oil; the sub-book was a declared subset under the bar and is flat.
- **The time-series cell** (+1.09 forward, +0.22 in sample) and the dollar book's forward
  number are recorded as what they are: unpredicted, one-season, one-root. Neither is a lead.

**Lesson, recorded:** the forward read was designed to predict the composition, and the
composition is what failed. A total that transfers at 70 % while its carriers reverse is the
signature of a rule that picks *something* every month and was lucky in sample about what; the
prediction to write, before any forward read of a cross-sectional book, is which names will
carry it, and to rank that above the Sharpe.
