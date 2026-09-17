# D468 RESULT — none of 24 session windows on eight roots clears the component standard; the observed best sits at the 78th percentile of its own family null; the ledger stays empty

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D468-RESULT-none-of-24-session-windows-on-eight-roots-clears-the-component-standard-the-best-sits-at-the-78th-percentile-of-its-family-null.md`. The H1 above is the full title.*

**Result of the pre-registered scoring in D468.** Runner `scripts/run_d468_wide_components.py`
(`--selftest` passes; `--run` under a minute), artefact `data/d468_wide_components.json`. All eight
D467 roots usable from 2016-01-04; in-sample **2016-01-04 to 2023-12-29**, a union calendar of
2,063 sessions; **2024-01 onward unread; no holdout spent.** No book was assembled, so
`d468_book_days.csv.gz` does not exist.

**Under [R15](../RULES.md#r15) this record closes nothing.** It reports what the family shows.

---

## 0. The headline

**Nothing enters.** The best of the 24 long constructions is ES-W1 (the full session held, one
MES, $3) at net Sharpe **+0.39 (SE 0.32)**, and **the common-sign family-maximum null puts the
best of 24 no-edge constructions at p50 +0.55, p95 +0.95 (SE 0.01): 77.7% of null draws beat
the observed best.** At the family level the 24 windows are indistinguishable from noise.

| construction | unit | sessions | net Sharpe (SE) | gross | short | mean $ | σ $ | cost / gross mean | hit | skew | worst $ |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ES-W1 18:00→16:00 | MES | 1,974 | **+0.39 (0.32)** | +0.64 | −0.89 | +7.69 | 183 | 39% | 52.5% | −0.26 | −1,344 |
| NQ-W1 | MNQ | 1,971 | +0.38 (0.32) | +0.54 | −0.69 | +10.13 | 287 | 30% | 54.2% | −0.31 | −1,975 |
| NQ-W2 18:00→09:00 | MNQ | 2,036 | +0.26 (0.28) | +0.56 | −0.85 | +5.59 | 158 | 54% | 54.2% | +0.10 | −798 |
| ES-W2 | MES | 2,039 | +0.19 (0.30) | +0.63 | −1.07 | +4.27 | 107 | 70% | 53.5% | +0.09 | −688 |
| YM-W1 | MYM | 1,969 | +0.15 (0.33) | +0.47 | −0.79 | +4.42 | 142 | 68% | 51.5% | −0.74 | −1,330 |
| NQ-W3 09:00→16:00 | MNQ | 1,972 | +0.10 (0.30) | +0.29 | −0.47 | +4.56 | 242 | 66% | 53.8% | −0.32 | −1,218 |
| YM-W2, ES-W3 | | | +0.04, +0.04 | +0.60, +0.35 | | | | 93%, 88% | | | |
| ZB-W1 / W2 / W3 | ZB, $6 | | +0.01, −0.08, −0.08 | +0.10, +0.05, +0.05 | | | 939, 686, 682 | | | | −8,350 |
| GC-W1 / W2 / W3 | MGC | | −0.23, −0.19, **−0.63** | +0.09, +0.25, −0.17 | | | | | | | |
| ZN-W1 / W2 / W3 | ZN, $6 | | −0.20, −0.29, −0.35 | +0.03, +0.03, −0.04 | | | | | | | |
| CL-W1 / W2 / W3 | MCL | | −0.39, −0.31, −0.69 | −0.09, +0.14, −0.30 | | | | | | | |
| 6E-W1 / W2 / W3 | M6E | | −0.72, −1.17, −0.85 | +0.01, −0.21, +0.24 | | | | | | | |

**The gross column is the finding.** Every index window is gross-positive at 0.3–0.65 and the
overnight leg (W2) is the larger part of it on all three index roots (ES +0.63 vs the day's
+0.35; NQ +0.56 vs +0.29; YM +0.60 vs +0.14): D259's overnight drift, on the futures, on three
roots, unchanged. **On every other root the gross edge is within ±0.3 of zero** — the treasuries,
gold, crude and the euro hold no session-window drift at this resolution in 2016–2023 — and
**the cost line then decides the rest**: $3 is 30–39% of the gross mean on ES-W1 and NQ-W1, 54–70%
on the overnight legs, and above 100% everywhere else. The short side is negative on all 24
(the short column), so nothing was missed by declaring long only.

**The shortest window is the one with the highest gross Sharpe and the lowest net.** ES-W2's
gross +0.63 equals ES-W1's +0.64 on 58% of the σ — the day leg adds variance and no return —
and its net is +0.19 against +0.39 because the same $3 is charged against a $4.27 mean instead
of $7.69. This is CLAUDE.md's cost-cutting-vs-edge-sharpening point inverted: the edge per unit
exposure is in the overnight leg, and the account cannot buy it at micro cost.

## 1. Correlations and the admission order

ρ(W2, W3) on the same root is **0.00 to −0.05 on all eight roots** (the two legs of a session are
independent to the SE, 0.02); σ² adds (ES: 107² + 149² ≈ 183²). ρ(ES-W1, NQ-W1) = 0.91,
ρ(ES-W1, YM-W1) = 0.92: the three index roots are one construction. Index against ZN/ZB W1 is
−0.11 / −0.17; GC and 6E against ES +0.07 / +0.20.

The order the standard produced, with the reasons: ES-W1 (+0.39, C-a), NQ-W1 (+0.38, C-a),
NQ-W2 (+0.26, C-a), ES-W2 (+0.19, C-a), YM-W1 (C-a, C-c skew −0.74), … ZB (C-a and C-d: σ $682–939
a day on one full contract is above the 1% expressibility bar — **ZB and ZN have no micro and
their unit is too large for a $50k account regardless of edge**), … 6E-W2 (−1.17). No entry, no
provisional entry, no book.

## 2. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a ES-W1 within ±0.03 of K1 +0.37 on 2,043 ± 10 sessions | | **+0.39 on 1,974** | Sharpe right; sessions 69 short — the holiday sessions (no 16:00 print; D449 took the 13:00 close) |
| X-b 1–4 clear C-a; family p95 +0.65..+0.90; 0–1 clear it | | **0**; **+0.95**; 0 | wrong on the count, p95 above the range: the family is more correlated in its noise than I allowed and none of it clears |
| X-c NQ-W1 +0.40..+0.70; GC-W2 +0.2..+0.5, GC-W3 < 0; ZN/ZB-W1 ≤ +0.2; CL-W1 ≤ 0; 6E-W1 ±0.3; W2 > W3 on the index | | NQ-W1 +0.38; GC-W2 **−0.19**, GC-W3 −0.63; ZN −0.20, ZB +0.01; CL −0.39; 6E **−0.72**; W2 > W3 on all three | NQ-W1 just under; the gold overnight pattern is **not** in 2016–2023 at micro cost (gross +0.25); 6E far below; the rest right |
| X-d ρ(W2,W3) < 0.15; index W1 > 0.85; index vs bonds −0.4..0; GC/6E < 0.3 | | 0.00–0.05; 0.91/0.92; −0.11/−0.17; 0.07/0.20 | all right |
| X-e book conditions | | no book | not testable |
| X-f under 2 min | | 0.0 min | right |

Two of the substantive predictions were wrong in the same direction as D466's: I expected
components where the standard found none. The family null was the right instrument and it
would have refused a +0.6 as readily as it refused +0.39.

## 3. What this leaves standing

- **The overnight index drift is real on the futures and unaffordable at micro size.** Gross
  Sharpe 0.5–0.65 on ES/NQ/YM W1 and W2; the $3 round trip on a $10–20k notional is 1.9–2.8 bp
  and takes 30–70% of the mean. The breakeven cost for C-a on ES-W1 is $1.48 (D466). This is
  the cost-failure branch; **no window, gate or root tested here changes it, and the plan's
  16:10 flat rule forbids the one thing that would (holding across sessions).**
- **The only lever left inside this family is notional per contract:** full-size ES at $17 is
  0.34 bp against the micro's 2 bp — K1 at one ES is net +0.48 in dollars (D466) — and the
  account cannot carry one ES night (σ ≈ $1,840 against a $2,000 floor; D463/D464). A larger
  account (150K) changes that arithmetic and not the edge.
- **Nothing here reads 2024+.** The slice stays unread until a component exists to confirm.
- The ledger's *Scored and NOT entered* table gains the 24 rows.

## 4. Files

Runner · `data/d468_wide_components.json` · the ledger rows · this record.
